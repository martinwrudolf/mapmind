from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Note, Notebook, User
from .src.ML import machine_learning as ml
from .src.spacing import spacing_alg as sp
from django.conf import settings
import json
from .src.aws import aws_connection as aws
import os
from spellchecker import SpellChecker
from mm.settings import BASE_DIR
import mm.settings
import compress_pickle
import pickle
import boto3
import glob
from smart_open import open
import json
import traceback

# Registration form
# https://studygyaan.com/django/how-to-create-sign-up-registration-view-in-django

# Password reset
# https://learndjango.com/tutorials/django-password-reset-tutorial
# https://www.sitepoint.com/django-send-email/
# https://www.geeksforgeeks.org/setup-sending-email-in-django-project/
# https://suhailvs.github.io/blog02.html#mail-setup-on-django-using-gmail
# https://stackoverflow.com/questions/73422664/django-email-sending-smtp-error-cant-send-a-mail
# https://stackoverflow.com/questions/10147455/how-to-send-an-email-with-gmail-as-provider-using-python/27515833#27515833

# Index page
def index(request):
    print("getting to nindexs")
    if not request.user.is_authenticated:
        return redirect('login')
    # Get the user
    user = request.user
    # Get the user's notebooks
    notebooks = Notebook.objects.filter(owner=user)
    # Get the user's notes
    notes = Note.objects.filter(owner=user)
    # Create a context
    context = {
        'notebooks': notebooks,
        'notes': notes
    }
    # Render the index page
    return render(request, 'mmapp/index.html', context)

# Redirect to Django provided login page
def login(request):
    if request.user.is_authenticated:
        return redirect('index')
    return redirect('login')

# Register page
# https://docs.djangoproject.com/en/4.1/topics/auth/passwords/#password-validation
# https://docs.djangoproject.com/en/4.1/topics/settings/
def register(request):
    print("etting to reegisteaf")
    if request.method == "GET":
        if request.user.is_authenticated:
            print("in register getasdfas")
            return redirect('')
        print("in register get")
        return render(request, 'registration/register.html')
    elif request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
       
        email = request.POST["email"]
        try:
            user = User.objects.get(username=username)
            return HttpResponse("Username is not unique!")
        except User.DoesNotExist:
            try: 
                user = User.objects.get(email=email)
                return HttpResponse("Email is not unique!")
            except User.DoesNotExist:
                newUser = User.objects.create_user(
                    username,
                    email,
                    password
                )
                try:
                    validate_password(password, newUser, None)
                    newUser.save()
                    return redirect('login')
                except ValidationError as error:
                    newUser.delete()
                    return HttpResponse(str(error.args[0]))
          
   
"""
Receive a file from the user and save it to the database as a Note.
"""
def upload(request):
    if not request.user.is_authenticated:
        return redirect('login')
    # Get the owner from the request
    print("in upload")
    owner = request.user
    if request.method == 'POST':
        print("if to post upload")
        accepted_content_types = ['text/plain',
                              'application/rtf',
                              'application/msword',
                              'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                              ]
        # TBD
        THRESHOLD = 20000
        try:
            # Get the file from the request
            print("request.FILES['file']", request.FILES['file'])
            print("request.POST['notebook']", request.POST['notebook'])
            file = request.FILES['file']
            if file.content_type not in accepted_content_types:
                return HttpResponse("File is not of correct format")
            if file.size > THRESHOLD:
                return HttpResponse("File is too large")
            
            notebook = request.POST['notebook']
            # Get the notebook from the database
            notebook = Notebook.objects.get(id=notebook, owner=owner)

            if Note.objects.filter(file_name=file.name,
                                   owner=owner,
                                   notebooks=notebook).exists():
                # note already exists
                return HttpResponse("Note file already exists")
            else:
                # note doesn't exist i notebook so must process notes
                MODEL_PATH = 'mmapp/ml_models/{0}'
                s3 = boto3.client("s3")

                path2glovekeys = MODEL_PATH.format('glove_keys.pkl')
                path2glove = MODEL_PATH.format('glove.pkl')
                # get original embeddings
                if len(glob.glob(path2glovekeys+"*")) == 0:
                    # glove words not there, need to redownload
                    aws.s3_download(s3, "glove_keys.pkl", path2glovekeys)

                glove_keys = ml.load_embeddings(path2glovekeys)
                oov, vocab, corpus = ml.process_user_notes(file, glove_keys)

                vocab_filename = str(owner.id)+"/"+notebook.name+"/"+file.name+"/vocab.txt"
                corpus_filename = str(owner.id)+"/"+notebook.name+"/"+file.name+"/corpus.txt"
                
                # save new note files
                aws.s3_write(s3, vocab_filename, vocab)
                aws.s3_write(s3, corpus_filename, corpus)

                try:
                    # load notebook vocab
                    notebook_vocab = aws.s3_read(s3, notebook.vocab)
                    # append new vocab to total notebook vocab
                    notebook_vocab += " "+vocab
                except:
                    # notebook did not have an associated vocab
                    return HttpResponse("Database error: Notebook does not have a vocab file")
                try:
                    notebook_corpus = aws.s3_read(s3, notebook.corpus)
                    notebook_corpus += " "+corpus
                except:
                    return HttpResponse("Database error: Notebook does not have a corpus file")

                notebook_oov = [word for word in notebook_vocab.split() if word not in glove_keys]
                notebook_oov += oov
                notebook_oov = list(set(notebook_oov))

                # save new notebook files
                aws.s3_write(s3, notebook.vocab, notebook_vocab.strip())
                aws.s3_write(s3, notebook.corpus, notebook_corpus.strip())

                # train model on notes
                # are there any new words?
                if len(oov) != 0:
                    coocc_arr = ml.create_cooccurrence(notebook_vocab, notebook_oov)

                    if len(glob.glob(path2glove)) == 0:
                        aws.s3_download(s3, "glove.pkl", path2glove)

                    embed = ml.load_embeddings(path2glove)
                    finetuned_embed = ml.train_mittens(coocc_arr, notebook_oov, embed)

                    # create kv object and save
                    kv = ml.create_kv_from_embed(finetuned_embed)
                    ml.save_kv(kv, MODEL_PATH.format(notebook.kv.replace("/","_")))

                    # upload all the files
                    print("would upload kv to s3 here")
                    aws.s3_upload(s3, MODEL_PATH.format(notebook.kv.replace("/","_")), notebook.kv)
                    aws.s3_upload(s3, MODEL_PATH.format(notebook.kv_vectors.replace("/","_")), notebook.kv_vectors)
                else:
                    print("no oov, no need for training")

                # Create a new Note assoicated with that notebook
                note = Note(file_name=file.name,
                            #file_content=file.read(),
                            file_type=file.content_type,
                            owner=owner,
                            notebooks=notebook,
                            vocab=vocab_filename,
                            corpus=corpus_filename)
                note.save()
                return HttpResponse("File uploaded successfully")
        except Notebook.DoesNotExist:
            return HttpResponse("Notebook does not exists")
        except:
            traceback.print_exc()
            return HttpResponse("Bad request")
    if request.method == 'GET':
        notebooks = Notebook.objects.filter(owner=owner)
        context = {
            "notebooks": notebooks
        }
        return render(request, 'mmapp/notebooks.html', context)
    
"""
Create a new notebook for the user.
"""
def create_notebook(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        # Get the notebook name from the request
        print("Request: ", request.POST)
        notebook = request.POST['notebook']
        # Get the owner from the request
        owner = request.user
        if Notebook.objects.filter(name=notebook,
                                   owner=owner).exists():
            # notebook already exists
            return HttpResponse("Notebook already exists")

        # Create paths to files for upload/download
        vocab_filename = str(owner.id)+"/"+notebook+"/vocab.txt"
        corpus_filename = str(owner.id)+"/"+notebook+"/corpus.txt"
        kv_filename = str(owner.id)+"/"+notebook+"/kv.kv"
        kv_vectors_filename = str(owner.id)+"/"+notebook+"/kv.kv.vectors.npy"
        # Create a new Notebook
        notebook = Notebook(name=notebook, 
                            owner=owner,
                            vocab=vocab_filename,
                            corpus=corpus_filename,
                            kv = kv_filename,
                            kv_vectors = kv_vectors_filename)
        # Save the Notebook
        notebook.save()

        # write empty files to s3 for this notebook
        s3 = boto3.client('s3')
        aws.s3_write(s3, vocab_filename, "")
        aws.s3_write(s3, corpus_filename, "")
        # Return a response
        return HttpResponse("Notebook created successfully")
    else:
        return HttpResponse("Notebook creation failed")
    
def delete_notebook(request):
    """Deletes a notebook and all notes associated with it."""
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        # Get the notebook name from the request
        notebook = request.POST['notebook']
        # Get the owner from the request
        owner = request.user
        # Delete the Notebook
        s3 = boto3.resource('s3')
        notebook = Notebook.objects.get(id=notebook)

        aws.s3_delete_folder(s3, str(owner.id)+'/'+notebook.name+'/')
        notebook.delete()

        # Return a response
        return HttpResponse("Notebook deleted successfully")

def delete_notes(request):
    """Deletes a note."""
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        # Get the note name from the request
        print("Request: ", request.POST)
        notes = request.POST.getlist('note')
        # Get the owner from the request
        owner = request.user
        s3 = boto3.resource('s3')
        notebooks_to_update = set()
        # Delete the Note
        for n in notes:
            n = Note.objects.get(id=n)
            aws.s3_delete_folder(s3, str(owner.id)+'/'+n.notebooks.name+'/'+n.file_name+'/')
            notebook = n.notebooks
            notebooks_to_update.add(notebook)
            n.delete()
        
        s3 = boto3.client('s3')
        for notebook in notebooks_to_update:
            # update notebooks files
            notes_list = Note.objects.filter(notebooks=notebook)
            aws.notebook_update_files(s3, notebook, notes_list)

            # need to retrain model
            MODEL_PATH = 'mmapp/ml_models/{0}'
            s3 = boto3.client("s3")
            path2glovekeys = MODEL_PATH.format('glove_keys.pkl')
            path2glove = MODEL_PATH.format('glove.pkl')
            # get original embeddings
            if len(glob.glob(path2glovekeys+"*")) == 0:
                # glove words not there, need to redownload
                aws.s3_download(s3, "glove_keys.pkl", path2glovekeys)

            glove_keys = ml.load_embeddings(path2glovekeys)
            
            try:
                # load notebook vocab
                notebook_vocab = aws.s3_read(s3, notebook.vocab)
            except:
                # notebook did not have an associated vocab
                return HttpResponse("Database error: Notebook does not have a vocab file")

            notebook_oov = [word for word in notebook_vocab.split() if word not in glove_keys]
            notebook_oov = list(set(notebook_oov))

            # train model on notes
            # are there any new words?
            if len(notebook_oov) != 0:
                coocc_arr = ml.create_cooccurrence(notebook_vocab, notebook_oov)

                if len(glob.glob(path2glove)) == 0:
                    aws.s3_download(s3, "glove.pkl", path2glove)

                embed = ml.load_embeddings(path2glove)
                finetuned_embed = ml.train_mittens(coocc_arr, notebook_oov, embed)

                # create kv object and save
                kv = ml.create_kv_from_embed(finetuned_embed)
                ml.save_kv(kv, MODEL_PATH.format(notebook.kv.replace("/","_")))

                # upload all the files
                print("would upload kv to s3 here")
                aws.s3_upload(s3, MODEL_PATH.format(notebook.kv.replace("/","_")), notebook.kv)
                aws.s3_upload(s3, MODEL_PATH.format(notebook.kv_vectors.replace("/","_")), notebook.kv_vectors)
            else:
                print("no oov, no need for training")
        # Return a response
        print("Notes deleted successfully")
    return HttpResponse("Notes deleted successfully")


# Placeholder response for now
def edit_notebook(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return HttpResponse(status=200, content="This is the URL where we edit notebooks!")

def merge_notebooks(request):
    """Merges notebooks into one notebook."""
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        # Get the notebook name from the request
        notebooks_to_merge = request.POST.getlist('notebooks[]')
        merged_notebook_name = request.POST['merged_notebook_name']
        print("Notebooks: ", notebooks_to_merge)
        print("Merged notebook name: ", merged_notebook_name)
        # Get the owner from the request
        owner = request.user
        # Create paths to files for upload/download
        vocab_filename = str(owner.id)+"/"+merged_notebook_name+"/vocab.txt"
        corpus_filename = str(owner.id)+"/"+merged_notebook_name+"/corpus.txt"
        kv_filename = str(owner.id)+"/"+merged_notebook_name+"/kv.kv"
        kv_vectors_filename = str(owner.id)+"/"+merged_notebook_name+"/kv.kv.vectors.npy"
        # Create a new Notebook
        if Notebook.objects.filter(name=merged_notebook_name,
                                   owner=owner).exists():
            # notebook already exists
            return HttpResponse("Notebook already exists")
        new_notebook = Notebook(name=merged_notebook_name, 
                            owner=owner,
                            vocab=vocab_filename,
                            corpus=corpus_filename,
                            kv = kv_filename,
                            kv_vectors = kv_vectors_filename)
        # Save the Notebook
        new_notebook.save()
        # Return a response
        s3_res = boto3.resource('s3')
        s3_client = boto3.client('s3')
        for n in notebooks_to_merge:
            n = Notebook.objects.get(id=n)
            notes = Note.objects.filter(notebooks=n)
            for note in notes:
                vocab_filename = str(owner.id)+"/"+new_notebook.name+"/"+note.file_name+"/vocab.txt"
                corpus_filename = str(owner.id)+"/"+new_notebook.name+"/"+note.file_name+"/corpus.txt"
                # create new note object under new notebook
                new_note = Note(file_name=note.file_name,
                        file_type=note.file_type, 
                        owner=owner,
                        notebooks=new_notebook,
                        vocab=vocab_filename,
                        corpus=corpus_filename)
                new_note.save()
                # move old note files into new notebook folder
                aws.move_file(s3_res, note.vocab, new_note.vocab)
                aws.move_file(s3_res, note.corpus, new_note.corpus)
            # need to delete old notebook data
            aws.s3_delete_folder(s3_res, str(owner.id)+'/'+n.name+'/')
            print("deleting notebook: ", n.name)
            n.delete()
        # update notebook files
        notes_list = Note.objects.filter(notebooks=new_notebook)
        aws.notebook_update_files(s3_client, new_notebook, notes_list)
        new_notebook.save()
        # need to train model for new notebook
        MODEL_PATH = 'mmapp/ml_models/{0}'
        path2glovekeys = MODEL_PATH.format('glove_keys.pkl')
        path2glove = MODEL_PATH.format('glove.pkl')
        # get original embeddings
        if len(glob.glob(path2glovekeys+"*")) == 0:
            # glove words not there, need to redownload
            aws.s3_download(s3_client, "glove_keys.pkl", path2glovekeys)

        glove_keys = ml.load_embeddings(path2glovekeys)
        
        try:
            # load notebook vocab
            notebook_vocab = aws.s3_read(s3_client, new_notebook.vocab)
        except:
            # notebook did not have an associated vocab
            return HttpResponse("Database error: Notebook does not have a vocab file")

        notebook_oov = [word for word in notebook_vocab.split() if word not in glove_keys]
        notebook_oov = list(set(notebook_oov))

        # train model on notes
        # are there any new words?
        if len(notebook_oov) != 0:
            coocc_arr = ml.create_cooccurrence(notebook_vocab, notebook_oov)

            if len(glob.glob(path2glove)) == 0:
                aws.s3_download(s3_client, "glove.pkl", path2glove)

            embed = ml.load_embeddings(path2glove)
            finetuned_embed = ml.train_mittens(coocc_arr, notebook_oov, embed)

            # create kv object and save
            kv = ml.create_kv_from_embed(finetuned_embed)
            ml.save_kv(kv, MODEL_PATH.format(new_notebook.kv.replace("/","_")))

            # upload all the files
            print("would upload kv to s3 here")
            aws.s3_upload(s3_client, MODEL_PATH.format(new_notebook.kv.replace("/","_")), new_notebook.kv)
            aws.s3_upload(s3_client, MODEL_PATH.format(new_notebook.kv_vectors.replace("/","_")), new_notebook.kv_vectors)
        else:
            print("no oov, no need for training")
        return HttpResponse("Notebooks merged successfully")

def notebooks(request):
    if not request.user.is_authenticated:
        return redirect('login')
    owner = request.user
    notebooks = Notebook.objects.filter(owner=owner)
    notes = Note.objects.filter(owner=owner)
    context = {
        "notebooks": notebooks,
        "notes": notes,
    }
    return render(request, "mmapp/notebooks.html", context)

def delete_notes(request):
    """Deletes a note."""
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        # Get the notebook name from the request
        print("Request: ", request.POST)
        notes = request.POST.getlist('note')
        # Get the owner from the request
        owner = request.user
        # Delete the Notebook
        for n in notes:
            n = Note.objects.get(id=n)
            n.delete()
        # Return a response
        print("Notes deleted successfully")
    return HttpResponse("Notes deleted successfully")


# Placeholder response for now
def edit_notebook(request):
    if not request.user.is_authenticated:
        return redirect('login')
        # return redirect('login')
    return HttpResponse(status=200, content="This is the URL where we edit notebooks!")


def notebooks(request):
    if not request.user.is_authenticated:
        return redirect('login')
    owner = request.user
    notebooks = Notebook.objects.filter(owner=owner)
    notes = Note.objects.filter(owner=owner)
    context = {
        "notebooks": notebooks,
        "notes": notes,
    }
    return render(request, "mmapp/notebooks.html", context)

# Placeholder response for now
def settings(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'mmapp/profile.html')

def edit_username(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponse(status=401)
        username = request.POST["username"]
        try:
            user = User.objects.get(username=username)
            return HttpResponse("Username is not unique!")
        except User.DoesNotExist:
            request.user.username = username
            request.user.save()
            return redirect('settings')
    else:
        return HttpResponse(status=405)
    
def edit_email(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponse(status=401)
        email = request.POST["email"]
        try: 
            user = User.objects.get(email=email)
            return HttpResponse("Email is not unique!")
        except User.DoesNotExist:
            request.user.email = email
            request.user.save()
            return redirect('settings')
    else:
        return HttpResponse(status=405)
    
def delete_account(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponse(status=401)
        try:
            user = User.objects.get(username=request.user.username)
            user.delete()
            return redirect('index')
        except User.DoesNotExist:
            # should never happen....but who knows?
            return HttpResponse(status=400)
    else:
        return HttpResponse(status=405)

def search(request):
    if not request.user.is_authenticated:
        return redirect('login')
    # Get the user
    user = request.user
    # Get the user's notebooks
    notebooks = Notebook.objects.filter(owner=user)
    context = {
        'notebooks' : notebooks
    }
    return render(request, "search/search.html", context)

def search_results(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user = request.user
    if request.method == 'GET' and not request.GET.get("search_words"):
        user = request.user
        # Get the user's notebooks
        notebooks = Notebook.objects.filter(owner=user)
        # Get the user's notes
        notes = Note.objects.filter(owner=user)
        context = {
            'notebooks': notebooks,
            'notes': notes
        }
        return render(request, "search/results.html", context)
    if request.method == 'GET' and request.GET.get("search_words"):
        query = request.GET.get("search_words").split()
        notebook_id = request.GET.get("notebook") if request.GET.get("notebook") else None
    if 'notesonly' in request.GET:
        notesonly = True
    else:
        notesonly = False
    if 'spellcheck' in request.GET:
        spellcheck = True
    else:
        spellcheck = False

    print("notesonly: ", notesonly)
    print("spellcheck: ", spellcheck)
    

    notebook = Notebook.objects.get(owner=user, id=notebook_id)

    s3 = boto3.client('s3')
    MODEL_PATH = 'mmapp/ml_models/{0}'
    path2glove = MODEL_PATH.format('glove.pkl')
    
    if notesonly:
        # load scrubbed vocab for this notebook
        try:
            # if this fails, then the user hasn't uploaded any notes into this notebook yet
            vocab = aws.s3_read(s3, notebook.vocab)
        except:
            vocab = None
    else:
        vocab = None
    if not os.path.exists('mmapp/ml_models'):
        print('making path')
        os.makedirs('mmapp/ml_models')
    # Check if kv object is stored locally
    if len(glob.glob(MODEL_PATH.format(notebook.kv.replace("/","_")))) == 0:
        # doesn't already exist so load it
        # download the files
        try:
            aws.s3_download(s3, notebook.kv, MODEL_PATH.format(notebook.kv.replace("/","_")))
            aws.s3_download(s3, notebook.kv_vectors, MODEL_PATH.format(notebook.kv_vectors.replace("/","_")))

            kv = ml.load_kv(MODEL_PATH.format(notebook.kv.replace('/','_')))
        except:
            # if we get here, the notebook hasn't been trained yet so just use GloVe
            if len(glob.glob(path2glove)) == 0:
                # need to load glove embeddings
                aws.s3_download(s3, "glove.pkl", path2glove)
            embed = ml.load_embeddings(path2glove)
            kv = ml.create_kv_from_embed(embed)
    else:
        kv = ml.load_kv(MODEL_PATH.format(notebook.kv.replace('/','_')))
    
    # spell check
    spell_checked = {}
    if spellcheck:
        spell = SpellChecker()
        misspelled = spell.unknown(query)
        
        for word in misspelled:
            correct_word = spell.correction(word)
            query.remove(word)
            query.append(correct_word)
            spell_checked[word] = correct_word

    # perform search
    res_matrix, words, skipwords = ml.search(query, kv, 1, vocab)
    # send results to spacing alg
    positions = sp.fruchterman_reingold(res_matrix)

    # create object of words and positions
    words_pos = {words[i]: positions[i] for i in range(len(words))}
    word_list = []
    for word in words_pos:
        word_list.append({"string":word, "pos":list(words_pos[word])})
    print(word_list)
    # https://stackoverflow.com/questions/43305020/how-to-use-the-context-variables-passed-from-django-in-javascript
    
    user = request.user
    notebooks = Notebook.objects.filter(owner=user)
    
    context = {
        "res": res_matrix,
        "words_pos": json.dumps(word_list),
        "spell_checked": spell_checked,
        "skipwords": skipwords,
        "notebooks": notebooks,
        "current_notebook": notebook,
    }
    return render(request, "search/results.html", context)

def inspect_node(request):
    # somehow get notebook_id from request
    body = json.loads(request.body)
    notebook_id =  body['notebook_id']
    searched_words = body['searched_words']
    clicked_word = body['word']
    print(notebook_id, searched_words, clicked_word)
    notebook = Notebook.objects.get(id=notebook_id)
    s3 = boto3.client('s3')
    user_notes = aws.s3_read(s3, notebook.corpus)
    print(user_notes)

    MODEL_PATH = 'mmapp/ml_models/{0}'
    path2glove = MODEL_PATH.format('glove.pkl')
    print(path2glove)
    if len(glob.glob(MODEL_PATH.format(notebook.kv.replace("/","_")))) == 0:
        # doesn't already exist so load it
        # download the files
        try:
            aws.s3_download(s3, notebook.kv, MODEL_PATH.format(notebook.kv.replace("/","_")))
            aws.s3_download(s3, notebook.kv_vectors, MODEL_PATH.format(notebook.kv_vectors.replace("/","_")))

            kv = ml.load_kv(MODEL_PATH.format(notebook.kv.replace('/','_')))
        except:
            # if we get here, the notebook hasn't been trained yet so just use GloVe
            if len(glob.glob(path2glove)) == 0:
                # need to load glove embeddings
                aws.s3_download(s3, "glove.pkl", path2glove)
            embed = ml.load_embeddings(path2glove)
            kv = ml.create_kv_from_embed(embed)
    else:
        kv = ml.load_kv(MODEL_PATH.format(notebook.kv.replace('/','_')))

    # do the inspection
    print(kv)
    results = ml.inspect_node(clicked_word, searched_words, user_notes, kv)
    print(results)
    return HttpResponse(status=200, content=json.dumps(results))


def results(request):
    if not request.user.is_authenticated:
        return redirect('login')
    # Get the user
    user = request.user
    # Get the user's notebooks
    notebooks = Notebook.objects.filter(owner=user)
    # Get the user's notes
    notes = Note.objects.filter(owner=user)
    context = {
        'notebooks': notebooks,
        'notes': notes
    }
    return render(request, "search/results.html", context)

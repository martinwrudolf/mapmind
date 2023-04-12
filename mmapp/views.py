from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
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
import pickle
import boto3
import glob
from smart_open import open
import json
import traceback

# Registration form sources:
# https://studygyaan.com/django/how-to-create-sign-up-registration-view-in-django

''' FR#4 -- Change.Password can be found in the password_reset html files '''
# Password reset HTML files: https://learndjango.com/tutorials/django-password-reset-tutorial

# Email and SMTP sources:
# https://www.sitepoint.com/django-send-email/
# https://www.geeksforgeeks.org/setup-sending-email-in-django-project/
# https://suhailvs.github.io/blog02.html#mail-setup-on-django-using-gmail
# https://stackoverflow.com/questions/73422664/django-email-sending-smtp-error-cant-send-a-mail
# https://stackoverflow.com/questions/10147455/how-to-send-an-email-with-gmail-as-provider-using-python/27515833#27515833

def index(request):
    """" Display the index page. """
    print("Got to index page.")
    if not request.user.is_authenticated:
        print("User not authenticated.")
        return redirect('login')
    user = request.user
    notebooks = Notebook.objects.filter(owner=user)
    notes = Note.objects.filter(owner=user)
    context = {
        'notebooks': notebooks,
        'notes': notes
    }
    print("Rendering index page with context ", context)
    return render(request, 'mmapp/index.html', context)

def login(request):
    """ Allow user to login to their account.

    Requirements:
        FR#3 -- Request.Login
    """
    if request.user.is_authenticated:
        print("User is authenticated. Sending to index.")
        return redirect('index')
    print("User is not authenticated. Sending to login.")
    return redirect('login')

# Register page sources:
# https://docs.djangoproject.com/en/4.1/topics/auth/passwords/#password-validation
# https://docs.djangoproject.com/en/4.1/topics/settings/
def register(request):
    ''' Register a new user. 
    
    Requirements:
        FR#1 -- Request.Registration
    '''
    print("Got to register page.")
    if request.method == "GET":
        print("Got to GET request.")
        if request.user.is_authenticated:
            print("User is authenticated. Sending to index.")
            return redirect('')
        print("User is not authenticated. Sending to register.")
        return render(request, 'registration/register.html')
    elif request.method == "POST":
        print("Got to POST request.")
        username = request.POST["username"]
        password = request.POST["password"]
        email = request.POST["email"]
        print("username", username, "password", password, "email", email)
        try:
            # check if username is unique
            user = User.objects.get(username=username)
            return HttpResponse(status=400, content="Username is not unique!")
        except User.DoesNotExist:
            try:
                # check if email is unique
                user = User.objects.get(email=email)
                return HttpResponse(status=400, content="Email is not unique!")
            except User.DoesNotExist:
                # create new user
                newUser = User.objects.create_user(
                    username,
                    email,
                    password
                )
                try:
                    validate_password(password, newUser, None)
                    newUser.save()
                    print("Creating new user, ", newUser)
                    return HttpResponse(status=201)
                except ValidationError as error:
                    newUser.delete()
                    return HttpResponse(status=400, content="Password is not valid!")
   
def upload(request):
    ''' Upload a note file.

    Requirements:
        FR#7 -- Upload.Notes
        FR#9 -- Edit.Notebook
    '''
    print("Got to upload page.")
    if not request.user.is_authenticated:
        print("User not authenticated.")
        return redirect('login')

    owner = request.user
    if request.method == 'POST':
        print("Got to POST request.")
        accepted_content_types = ['text/plain',
                              'application/rtf',
                              'application/msword',
                              'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                              ]
        # maximum file size = 450KB
        THRESHOLD = 450000
        try:
            # Get the file from the request
            file = request.FILES['file']
            if file.content_type not in accepted_content_types:
                print(f"File {file.name} is not of correct format")
                return HttpResponse(status=400, content="File is not of correct format")
            if file.size > THRESHOLD:
                print(f"File {file.name} is too large")
                return HttpResponse(status=400, content="File is too large")
            
            # get notebook to upload notes into
            notebook = request.POST['notebook']
            notebook = Notebook.objects.get(id=notebook, owner=owner)
            print("notebook", notebook)
            if Note.objects.filter(file_name=file.name,
                                   owner=owner,
                                   notebooks=notebook).exists():
                print(f"Note file {file.name} already exists in this notebook")
                return HttpResponse(status=400, content="Note file already exists in this notebook")
            else:
                # note doesn't exist in notebook so must process notes
                MODEL_PATH = 'mmapp/ml_models/{0}'
                path2glovekeys = MODEL_PATH.format('glove_keys.pkl')
                
                # get glove keys
                if len(glob.glob(path2glovekeys+"*")) == 0:
                    # glove words not there, need to redownload
                    # If mmapp/ml_models doesn't exist, create it
                    if not os.path.exists('mmapp/ml_models'):
                        os.makedirs('mmapp/ml_models')

                    aws.s3_download("glove_keys.pkl", path2glovekeys)
                    print("Downloaded glove.pkl from s3 to ", path2glovekeys)

                # load keys and process notes
                glove_keys = ml.load_embeddings(path2glovekeys)
                oov, vocab, corpus, pics_or_tables = ml.process_user_notes(file, glove_keys)

                vocab_filename = (str(owner.id)+"/"+notebook.name+"/"+file.name+"/vocab.txt").replace(" ", "_")
                corpus_filename = (str(owner.id)+"/"+notebook.name+"/"+file.name+"/corpus.txt").replace(" ", "_")
                
                # save new note files
                print(f"Saving {vocab_filename} and {corpus_filename} to s3")
                aws.s3_write(vocab_filename, vocab)
                aws.s3_write(corpus_filename, corpus)

                try:
                    # load notebook vocab
                    notebook_vocab = aws.s3_read(notebook.vocab)
                    # append new vocab to total notebook vocab
                    notebook_vocab += " "+vocab
                except:
                    # notebook did not have an associated vocab
                    print(f"Notebook {notebook} did not have an associated vocab")
                    return HttpResponse(status=400,
                                        content="Database error: Notebook does not have a vocab file")
                try:
                    # load notebook corpus
                    notebook_corpus = aws.s3_read(notebook.corpus)
                    notebook_corpus += " "+corpus
                except:
                    print(f"Notebook {notebook} did not have an associated corpus")
                    return HttpResponse(status=400,
                                        content="Database error: Notebook does not have a corpus file")

                notebook_oov = [word for word in notebook_vocab.split() if word not in glove_keys]
                notebook_oov += oov
                notebook_oov = list(set(notebook_oov))

                # save new notebook files
                aws.s3_write(notebook.vocab, notebook_vocab.strip())
                aws.s3_write(notebook.corpus, notebook_corpus.strip())

                # train model on notes
                # are there any new words?
                if len(oov) != 0:
                    # train the model on ec2
                    #train_model(notebook_vocab, notebook_oov, notebook.kv, notebook.kv_vectors)
                    aws.train_on_ec2(notebook.vocab, notebook.kv, notebook.kv_vectors)
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
                print(f"Note {note} saved to database")
                if pics_or_tables:
                    return HttpResponse(status=200, content="There were pictures and/or tables that were disregarded. File uploaded successfully!")
                return HttpResponse(status=200, content="File uploaded successfully")
        except Notebook.DoesNotExist:
            print("Notebook does not exists")
            return HttpResponse(status=400, content="Notebook does not exists")
        except Exception as e:
            print("Bad request")
            print("Unexpected error:", e)
            return HttpResponse(status=400, content="Bad request")
    if request.method == 'GET':
        notebooks = Notebook.objects.filter(owner=owner)
        context = {
            "notebooks": notebooks
        }
        print("Rendering notebooks.html with context: ", context)
        return render(request, 'mmapp/notebooks.html', context)

def create_notebook(request):
    ''' Create a new notebook.

    Requirements:
        FR#8 -- Create.Notebook
    '''
    if not request.user.is_authenticated:
        return HttpResponse(status=401)
    if request.method == 'POST':
        # Get the notebook name from the request
        print("Request: ", request.POST)
        notebook = request.POST['notebook']
        # Get the owner from the request
        owner = request.user
        if Notebook.objects.filter(name=notebook,
                                   owner=owner).exists():
            # notebook already exists
            return HttpResponse(status=400, content="Notebook already exists")

        # Create paths to files for upload/download
        vocab_filename = (str(owner.id)+"/"+notebook+"/vocab.txt").replace(" ", "_")
        corpus_filename = (str(owner.id)+"/"+notebook+"/corpus.txt").replace(" ", "_")
        kv_filename = (str(owner.id)+"/"+notebook+"/kv.kv").replace(" ", "_")
        kv_vectors_filename = (str(owner.id)+"/"+notebook+"/kv.kv.vectors.npy").replace(" ", "_")
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
        aws.s3_write(vocab_filename, "")
        aws.s3_write(corpus_filename, "")

        # Return a response
        return HttpResponse(status=201, content="Notebook created successfully")
    else:
        return HttpResponse(status=405)
    
def delete_notebook(request):
    ''' Delete a notebook and all associate note files.

    Requirements:
        FR#10 -- Delete.Notebook
    '''
    if not request.user.is_authenticated:
        return HttpResponse(status=401)
    if request.method == 'POST':
        # Get the notebook name from the request
        notebook = request.POST['notebook']
        # Get the owner from the request
        owner = request.user
        # Delete the Notebook
        notebook = Notebook.objects.get(id=notebook)

        # delete from s3
        aws.s3_delete_folder((str(owner.id)+'/'+notebook.name+'/').replace(" ", "_"))

        # delete from database
        notebook.delete()

        # Return a response
        return HttpResponse(status=201, content="Notebook deleted successfully")
    else:
        return HttpResponse(status=405)

def delete_notes(request):
    ''' Delete a note file.

    Requirements:
        FR#9 -- Edit.Notebook
    '''
    if not request.user.is_authenticated:
        return HttpResponse(status=401)
    if request.method == 'POST':
        # Get the note name from the request
        print("Request: ", request.POST)
        notes = request.POST.getlist('note')
        # Get the owner from the request
        owner = request.user
        notebooks_to_update = set()
        # Delete the Note
        for n in notes:
            n = Note.objects.get(id=n)
            aws.s3_delete_folder((str(owner.id)+'/'+n.notebooks.name+'/'+n.file_name+'/').replace(" ", "_"))
            notebook = n.notebooks
            notebooks_to_update.add(notebook)
            n.delete()

        for notebook in notebooks_to_update:
            # update notebooks files
            notes_list = Note.objects.filter(notebooks=notebook)
            try:
                aws.notebook_update_files(notebook, notes_list)
            except:
                print("error updating notebook files")

            # need to retrain model
            MODEL_PATH = 'mmapp/ml_models/{0}'
            path2glovekeys = MODEL_PATH.format('glove_keys.pkl')
            # get original embeddings
            if len(glob.glob(path2glovekeys+"*")) == 0:
                if not os.path.exists('mmapp/ml_models'):
                        os.makedirs('mmapp/ml_models')
                # glove words not there, need to redownload
                aws.s3_download("glove_keys.pkl", path2glovekeys)

            glove_keys = ml.load_embeddings(path2glovekeys)

            try:
                # load notebook vocab
                notebook_vocab = aws.s3_read(notebook.vocab)
            except:
                # notebook did not have an associated vocab
                return HttpResponse("Database error: Notebook does not have a vocab file")

            notebook_oov = [word for word in notebook_vocab.split() if word not in glove_keys]
            notebook_oov = list(set(notebook_oov))

            # train model on notes
            # are there any new words?
            if len(notebook_oov) != 0:
                # train in background
                print("training model")
                print("notebook.kv: ", notebook.kv)
                print("notebook.kv_vectors: ", notebook.kv_vectors)
                #train_model(notebook_vocab, notebook_oov, notebook.kv, notebook.kv_vectors)
                aws.train_on_ec2(notebook.vocab, notebook.kv, notebook.kv_vectors)
            else:
                print("no oov, no need for training")
        # Return a response
        print("Notes deleted successfully")
        return HttpResponse(status=200, content="Notes deleted successfully")
    else:
        return HttpResponse(status=405)


# Placeholder response for now
def edit_notebook(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return HttpResponse(status=200, content="This is the URL where we edit notebooks!")


def merge_notebooks(request):
    ''' Merge several notebooks into one.

    Requirements:
        FR#11 -- Merge.Notebook
    '''
    if not request.user.is_authenticated:
        return HttpResponse(status=401)
    if request.method == 'POST':
        # Get the notebook name from the request
        notebooks_to_merge = request.POST.getlist('notebooks[]')
        merged_notebook_name = request.POST['merged_notebook_name']
        print("Notebooks: ", notebooks_to_merge)
        print("Merged notebook name: ", merged_notebook_name)
        # Get the owner from the request
        owner = request.user
        # Create paths to files for upload/download
        vocab_filename = (str(owner.id)+"/"+merged_notebook_name+"/vocab.txt").replace(" ", "_")
        corpus_filename = (str(owner.id)+"/"+merged_notebook_name+"/corpus.txt").replace(" ", "_")
        kv_filename = (str(owner.id)+"/"+merged_notebook_name+"/kv.kv").replace(" ", "_")
        kv_vectors_filename = (str(owner.id)+"/"+merged_notebook_name+"/kv.kv.vectors.npy").replace(" ", "_")
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
        for n in notebooks_to_merge:
            n = Notebook.objects.get(id=n)
            notes = Note.objects.filter(notebooks=n)
            for note in notes:
                vocab_filename = (str(owner.id)+"/"+new_notebook.name+"/"+note.file_name+"/vocab.txt").replace(" ", "_")
                corpus_filename = (str(owner.id)+"/"+new_notebook.name+"/"+note.file_name+"/corpus.txt").replace(" ", "_")
                # create new note object under new notebook
                new_note = Note(file_name=note.file_name,
                        file_type=note.file_type, 
                        owner=owner,
                        notebooks=new_notebook,
                        vocab=vocab_filename,
                        corpus=corpus_filename)
                new_note.save()
                # move old note files into new notebook folder
                print("moving vocab files: ", note.vocab, " to ", new_note.vocab)
                print("moving corpus files: ", note.corpus, " to ", new_note.corpus)
                aws.move_file(note.vocab, new_note.vocab)
                aws.move_file(note.corpus, new_note.corpus)
            # need to delete old notebook data
            # happens in background
            print("deleting notebook folder: ", str(owner.id)+'/'+n.name+'/'.replace(" ", "_"))
            aws.s3_delete_folder((str(owner.id)+'/'+n.name+'/').replace(" ", "_"))
            print("deleting notebook: ", n.name)
            n.delete()
        # update notebook files
        notes_list = Note.objects.filter(notebooks=new_notebook)

        try:
            aws.notebook_update_files(new_notebook, notes_list)
        except:
            print("error updating notebook files")
        new_notebook.save()
        # need to train model for new notebook
        MODEL_PATH = 'mmapp/ml_models/{0}'
        path2glovekeys = MODEL_PATH.format('glove_keys.pkl')
        # get original embeddings
        if len(glob.glob(path2glovekeys+"*")) == 0:
            if not os.path.exists('mmapp/ml_models'):
                        os.makedirs('mmapp/ml_models')
            # glove words not there, need to redownload
            aws.s3_download("glove_keys.pkl", path2glovekeys)

        glove_keys = ml.load_embeddings(path2glovekeys)
        
        try:
            # load notebook vocab
            notebook_vocab = aws.s3_read(new_notebook.vocab)
        except:
            # notebook did not have an associated vocab, so it must still be uploading
            return HttpResponse("Database error: Notebook does not have a vocab file")

        notebook_oov = [word for word in notebook_vocab.split() if word not in glove_keys]
        notebook_oov = list(set(notebook_oov))

        # train model on notes
        # are there any new words?
        if len(notebook_oov) != 0:
            # train model in background
            #train_model(notebook_vocab, notebook_oov, new_notebook.kv, new_notebook.kv_vectors)
            aws.train_on_ec2(new_notebook.vocab, new_notebook.kv, new_notebook.kv_vectors)
        else:
            print("no oov, no need for training")
        return HttpResponse(status=201, content="Notebooks merged successfully")
    else:
        return HttpResponse(status=405)

def notebooks(request):
    ''' Main Notebooks page. '''
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
    ''' Settings page '''
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'mmapp/profile.html')

def edit_username(request):
    ''' Allow user to edit their username.

    Requirements:
        FR#5 -- Change.Username
    '''
    if request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponse(status=401)
        username = request.POST["username"]
        try:
            user = User.objects.get(username=username)
            return HttpResponse(status=400, content="Username is not unique!")
        except User.DoesNotExist:
            request.user.username = username
            request.user.save()
            return HttpResponse(status=201, content="Username edited successfully!")
    else:
        return HttpResponse(status=405)
    
def edit_email(request):
    ''' Allow user to edit their email address.

    Requirements:
        FR#6 -- Change.Email
    '''
    if request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponse(status=401)
        email = request.POST["email"]
        try: 
            user = User.objects.get(email=email)
            return HttpResponse(status=400, content="Email is not unique!")
        except User.DoesNotExist:
            request.user.email = email
            request.user.save()
            return HttpResponse(status=201, content="Email edited succesfully")
    else:
        return HttpResponse(status=405)
    
def delete_account(request):
    ''' Delete user account.

    Requirements:
        FR#2 -- Delete.Account
    '''
    if request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponse(status=401)
        try:
            user = User.objects.get(username=request.user.username)
            user_id = user.id
            try:
                aws.s3_delete_folder(str(user_id) + '/')
                user.delete()
            except:
                user.delete()
            return HttpResponse(status=200)
        except User.DoesNotExist:
            # should never happen....but who knows?
            return HttpResponse(status=400)
    else:
        return HttpResponse(status=405)

def search(request):
    ''' Old search page - deprecated '''
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
    ''' Search and visualization page.

    Requirements:
        FR#12 -- Search.Word
        FR#13 -- Update.Search
        FR#14 -- Change.Notebook
        FR#15 -- Visualization.Zoom
        FR#16 -- Visualization.Rotate
    '''
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
            'notes': notes,
            'error': False,
            'errorMsg': ""
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

    unique_filename = aws.search_on_ec2(query, notebook.kv, notebook.kv_vectors, notebook.vocab, spellcheck, notesonly)
    print(unique_filename)
    if unique_filename == 'error\n':
        # there was a problem
        context = {
            "notebooks": notebooks,
            "current_notebook": notebook,
            "error": True,
            "errorMsg": "Error! Something wrong with ec2 search"
        }
        return render(request, "search/results.html", context)
    search_results = ml.load_embeddings(unique_filename)
    print(search_results)
    # send results to spacing alg
    res_matrix = search_results['res_matrix']
    words = search_results['words']
    skipwords = search_results['skipwords']
    spell_checked = search_results['spell_checked']
    positions = sp.fruchterman_reingold(res_matrix)

    # create object of words and positions
    words_pos = {words[i]: positions[i] for i in range(len(words))}
    word_list = []
    # Source: https://stackoverflow.com/questions/43305020/how-to-use-the-context-variables-passed-from-django-in-javascript
    for word in words_pos:
        word_list.append({"string":word, "pos":list(words_pos[word])})
    print(word_list)

    user = request.user
    notebooks = Notebook.objects.filter(owner=user)
    if (len(skipwords) > 0 and skipwords[0]== None):
        skipwords = []

    context = {
        "res": res_matrix,
        "words_pos": json.dumps(word_list),
        "spell_checked": spell_checked,
        "skipwords": json.dumps(skipwords),
        "notebooks": notebooks,
        "current_notebook": notebook,
        "error": False,
        "errorMsg": ""
    }
    return render(request, "search/results.html", context)

def inspect_node(request):
    ''' Inspect a node when the user clicks on it.

    Requirements:
        FR#17 -- Inspect.Node
    '''
    # somehow get notebook_id from request
    body = json.loads(request.body)
    notebook_id =  body['notebook_id']
    searched_words = body['searched_words']
    clicked_word = body['word']
    print(notebook_id, searched_words, clicked_word)
    notebook = Notebook.objects.get(id=notebook_id)
    results = aws.inspect_on_ec2(clicked_word, searched_words, notebook.corpus, notebook.kv, notebook.kv_vectors)
    if len(results) == 1 and results[0] == "":
        results = []
    print(results)
    return HttpResponse(status=200, content=json.dumps(results))


def results(request):
    ''' Deprecated '''
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

#@background(schedule=10)
def train_model(vocab, oov, kv_path, kv_vectors_path):
    ''' Deprecated '''
    MODEL_PATH = 'mmapp/ml_models/{0}'
    path2glove = MODEL_PATH.format('glove.pkl')
    #resp = ec2.send_command(InstanceIds=["i-063cef059dc0f3ca7"], DocumentName="AWS-RunShellScript", Parameters={'commands':["su ec2-user", "cd /home/ec2-user", "source /home/ec2-user/mapmind/env/bin/activate", "python3 train_model.py 3/demonotebook/vocab.txt 3/demonotebook/kv.kv 3/demonotebook/kv.kv.vectors.npy"]})
    coocc_arr = ml.create_cooccurrence(vocab, oov)
    if len(glob.glob(path2glove)) == 0:
        aws.s3_download("glove.pkl", path2glove)

    print('loading embed')
    embed = ml.load_embeddings(path2glove)
    print('loaded embed')
    finetuned_embed = ml.train_mittens(coocc_arr, oov, embed)
    print('trained')
    print('creating kv')
    # create kv object and save
    kv = ml.create_kv_from_embed(finetuned_embed)
    print('made kv')
    print('saving kv')
    ml.save_kv(kv, MODEL_PATH.format(kv_path.replace("/","_")))
    print('saved kv')
    # upload all the files
    print("upload kv to s3 here")
    # this will happen in background
    print("upload kv_vectors to s3 here")
    print("kv_path: ", kv_path)
    print("kv_vectors_path: ", kv_vectors_path)
    print('MODEL_PATH.format(kv_path.replace("/","_")): ', MODEL_PATH.format(kv_path.replace("/","_")))
    print('MODEL_PATH.format(kv_vectors_path.replace("/","_")): ', MODEL_PATH.format(kv_vectors_path.replace("/","_")))
    aws.s3_upload(MODEL_PATH.format(kv_path.replace("/","_")), kv_path)
    aws.s3_upload(MODEL_PATH.format(kv_vectors_path.replace("/","_")), kv_vectors_path)
    print("uploaded kv to s3")
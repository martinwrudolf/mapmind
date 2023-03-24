from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from .models import Note, Notebook
from .src.ML import machine_learning as ml
from .src.spacing import spacing_alg as sp
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

# Index page
def index(request):
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
    
"""
Receive a file from the user and save it to the database as a Note.
"""
def upload(request):
    if not request.user.is_authenticated:
        return redirect('login')
    # Get the owner from the request
    owner = request.user
    if request.method == 'POST':
        accepted_content_types = ['text/plain',
                              'application/rtf',
                              'application/msword',
                              'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                              ]
        # TBD
        THRESHOLD = 20000
        # print("request", request)
        # print("request.FILES", request.FILES)
        # print("request.post", request.POST)
        try:
            # Get the file from the request
            file = request.FILES['file']
            if file.content_type not in accepted_content_types:
                return HttpResponse("File is not of correct format")
            if file.size > THRESHOLD:
                return HttpResponse("File is too large")
            
            notebook = request.POST['notebook']
            print("request post")
            # Get the notebook from the database
            notebook = Notebook.objects.get(id=notebook, owner=owner)
            print("got notebook")

            if Note.objects.filter(file_name=file.name,
                                   owner=owner,
                                   notebooks=notebook).exists():
                # note already exists
                print("Note file already exists!")
                """ note_obj = Note.objects.get(file_name=notebook, owner=owner)
                if notebook not in note_obj.notebooks:
                    note_obj.notebooks.append(notebook)
                note_obj.save() """
                return HttpResponse("Note file already exists")
            else:
                # note doesn't exist i notebook so must process notes
                MODEL_PATH = 'mmapp/ml_models/{0}'
                s3 = boto3.client("s3")
                params = {'client': s3}
                print("created client")
                path2glovekeys = MODEL_PATH.format('glove_keys.pkl')
                path2glove = MODEL_PATH.format('glove.pkl')
                # get original embeddings
                if len(glob.glob(path2glovekeys+"*")) == 0:
                    # glove words not there, need to redownload
                    """ with open('s3://mapmind-ml-models/embed.pkl', mode='rb', transport_params=params) as f:
                        embed = pickle.load(f) """
                    
                    s3.download_file(Bucket="mapmind-ml-models", Key="glove_keys.pkl", Filename=path2glovekeys)
                    print("success")

                glove_keys = ml.load_embeddings(path2glovekeys)
                print("loaded keys")
                oov, vocab, corpus = ml.process_user_notes(file, glove_keys)
                print("processed user notes")

                vocab_filename = str(owner.id)+"/"+notebook.name+"/"+file.name+"/vocab.txt"
                corpus_filename = str(owner.id)+"/"+notebook.name+"/"+file.name+"/corpus.txt"
                # save new notebook files
                with open('s3://mapmind-ml-models/'+vocab_filename, mode='w', transport_params=params) as f:
                    f.write(vocab)
                with open('s3://mapmind-ml-models/'+corpus_filename, mode='w', transport_params=params) as f:
                    f.write(corpus)
                print("note files saved")

                try:
                    # load notebook corpus and vocab
                    with open('s3://mapmind-ml-models/'+notebook.vocab, mode='r',transport_params=params) as f:
                        notebook_vocab = f.read()
                    print('read vocab')
                    with open('s3://mapmind-ml-models/'+notebook.corpus, mode='r',transport_params=params) as f:
                        notebook_corpus = f.read()
                    print('read notebook files')

                    notebook_vocab += " "+vocab
                    notebook_corpus += " "+corpus
                    print(notebook_vocab)
                except:
                    # notebook did not have an associated oov so we'll assume it has nothing
                    notebook_vocab = vocab
                    notebook_corpus = corpus

                notebook_oov = [word for word in notebook_vocab.split() if word not in glove_keys]
                notebook_oov += oov
                notebook_oov = list(set(notebook_oov))
                print(notebook_oov)
                print(notebook_vocab)
                print(notebook_corpus)
                print('created new notebook info')
                # save new notebook files
                with open('s3://mapmind-ml-models/'+notebook.vocab, mode='w', transport_params=params) as f:
                    f.write(notebook_vocab)
                with open('s3://mapmind-ml-models/'+notebook.corpus, mode='w', transport_params=params) as f:
                    f.write(notebook_corpus)
                print('saved notebook files')
                # train model on notes
                # are there any new words?
                if len(oov) != 0:
                    coocc_arr = ml.create_cooccurrence(notebook_vocab, notebook_oov)
                    print("made matrix")

                    if len(glob.glob(path2glove)) == 0:
                        s3.download_file(Bucket="mapmind-ml-models", Key="glove.pkl", Filename=path2glove)
                        print("downloaded glove")

                    embed = ml.load_embeddings(path2glove)
                    finetuned_embed = ml.train_mittens(coocc_arr, notebook_oov, embed)
                    print('training done')
                    # create kv object and save
                    kv = ml.create_kv_from_embed(finetuned_embed)
                    print('created kv')
                    ml.save_kv(kv, MODEL_PATH.format(notebook.kv.replace("/","_")))
                    print('model saved')
                    # upload all the files
                    s3.upload_file(Bucket="mapmind-ml-models", Key=notebook.kv, Filename = MODEL_PATH.format(notebook.kv.replace("/","_")))
                    s3.upload_file(Bucket="mapmind-ml-models", Key=notebook.kv_vectors, Filename = MODEL_PATH.format(notebook.kv_vectors.replace("/","_")))
                    print('model uploaded')
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
                print("made note object")
                note.save()
                print("saved note")
                return HttpResponse("File uploaded successfully")
        except Notebook.DoesNotExist:
            return HttpResponse("Notebook does not exists")
        """ except:
            return HttpResponse("Bad request") """
    if request.method == 'GET':
        notebooks = Notebook.objects.filter(owner=owner)
        context = {
            "notebooks": notebooks
        }
        return render(request, 'mmapp/upload.html', context)
    
"""
Create a new notebook for the user.
"""
def create_notebook(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        # Get the notebook name from the request
        notebook = request.POST['notebook']
        # Get the owner from the request
        owner = request.user
        if Notebook.objects.filter(name=notebook,
                                   owner=owner).exists():
            # notebook already exists
            return HttpResponse("Notebook already exists")

        # Create paths to files for upload/download
        vocab_filename = str(owner.id)+"/"+notebook+"/vocab.txt"
        vocab_local = 'mmapp/ml_models/{0}'.format(vocab_filename)
        corpus_filename = str(owner.id)+"/"+notebook+"/corpus.txt"
        corpus_local = 'mmapp/ml_models/{0}'.format(corpus_filename)
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

        notes = Note.objects.filter(notebooks=notebook)
        for note in notes:
            print(note)
            s3.Object('mapmind-ml-models', note.vocab).delete()
            s3.Object('mapmind-ml-models', note.corpus).delete()
            print("deleted " + note.file_name)
        s3.Object('mapmind-ml-models', notebook.vocab).delete()
        s3.Object('mapmind-ml-models', notebook.corpus).delete()
        s3.Object('mapmind-ml-models', notebook.kv).delete()
        s3.Object('mapmind-ml-models', notebook.kv_vectors).delete()
        notebook.delete()

        # Return a response
        return HttpResponse("Notebook deleted successfully")

    
# Do we need this to return a register page or does Django have a built in register route?
def register(request):
    if request.user.is_authenticated:
        return redirect('index')
    return HttpResponse(status=200, content="This is where we register users!")

# Placeholder response for now
def edit_notebook(request):
    if not request.user.is_authenticated:
        return redirect('login')
        # return redirect('login')
    return HttpResponse(status=200, content="This is the URL where we edit notebooks!")

# Placeholder response for now
def settings(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return HttpResponse(status=200, content="This is the URL where the settings page will be!")

def search(request):
    if not request.user.is_authenticated:
        return redirect('login')
    #template = loader.get_template("search/search.html")
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
    template = loader.get_template("search/search_results.html")
    user = request.user
    if request.method == 'GET' and request.GET.get("search_words"):
        query = request.GET.get("search_words").split()
        notebook_id = request.GET.get("notebook")
        print(notebook_id)
    if 'notesonly' in request.GET:
        notesonly = True
    else:
        notesonly = False
    if 'spellcheck' in request.GET:
        spellcheck = True
    else:
        spellcheck = False

    notebook = Notebook.objects.get(owner=user, id=notebook_id)

    s3 = boto3.client('s3')
    params = {'client': s3}
    MODEL_PATH = 'mmapp/ml_models/{0}'
    path2glove = MODEL_PATH.format('glove.pkl')

    # load scrubbed vocab for this notebook
    """ print("BASE_DIR", BASE_DIR)
    print(os.path.join(BASE_DIR, 'mmapp/src/ML/vocab_scrubbed.pkl')) """
    
    if notesonly:
        # load scrubbed vocab for this notebook
        # FOR NOW: REPLACE THE FOLLOWING PATH WITH THE PATH TO THE VOCAB_SCRUBBED ON YOUR LOCAL MACHINE
        #vocab = ml.load_embeddings(os.path.join(BASE_DIR, 'mmapp/src/ML/vocab_scrubbed.pkl'))
        #vocab = ml.load_embeddings(r"C:\Users\clair\Documents\Year 5\ECE 493\Project\Testing_ML\mapmind\mm\mmapp\src\ML\vocab_scrubbed.pkl")
        try:
            # if this fails, then the user hasn't uploaded any notes into this notebook yet
            """ with open('s3://mapmind-ml-models/'+notebook.oov, mode='r',transport_params=params) as f:
                oov = f.read()
            print('read oov') """
            with open('s3://mapmind-ml-models/'+notebook.vocab, mode='r',transport_params=params) as f:
                vocab = f.read()
            print('read vocab')
            """ with open('s3://mapmind-ml-models'+notebook.corpus, mode='r',transport_params=params) as f:
                corpus = f.read()
            print('read corpus') """
        except:
            vocab = None
    else:
        vocab = None

    # Check if kv object is stored locally
    if len(glob.glob(MODEL_PATH.format(notebook.kv.replace("/","_")))) == 0:
        # doesn't already exist so load it
        # download the files
        try:
            s3.download_file(Bucket="mapmind-ml-models", Key=notebook.kv, Filename = MODEL_PATH.format(notebook.kv.replace("/","_")))
            s3.download_file(Bucket="mapmind-ml-models", Key=notebook.kv_vectors, Filename = MODEL_PATH.format(notebook.kv_vectors.replace("/","_")))
            print("downloaded")
            kv = ml.load_kv(MODEL_PATH.format(notebook.kv.replace('/','_')))
            print("loaded kv")
        except:
            # if we get here, the notebook hasn't been trained yet so just use GloVe
            if len(glob.glob(path2glove)) == 0:
                # need to load glove embeddings
                s3.download_file(Bucket="mapmind-ml-models", Key="glove.pkl", Filename=path2glove)
            embed = ml.load_embeddings(path2glove)
            kv = ml.create_kv_from_embed(embed)
    else:
        kv = ml.load_kv(MODEL_PATH.format(notebook.kv.replace('/','_')))
        print("loaded kv")
    
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
            print(word)

    # perform search
    res_matrix, words, skipwords = ml.search(query, kv, 1, vocab)
    print(res_matrix)
    print(skipwords)
    # send results to spacing alg
    positions = sp.fruchterman_reingold(res_matrix)
    #print(res)
    #words = [line[0] for line in res]

    # create object of words and positions
    words_pos = {words[i]: positions[i] for i in range(len(words))}
    #print(words_pos)
    context = {
        "res": res_matrix,
        "words_pos": words_pos,
        "spell_checked": spell_checked,
        "skipwords": skipwords
    }

    return render(request, "search/search_results.html", context)

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

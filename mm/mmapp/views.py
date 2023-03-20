from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from .models import Note, Notebook
from .src.ML import machine_learning as ml
from .src.spacing import spacing_alg as sp
import os
from spellchecker import SpellChecker

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
            # Get the notebook from the database
            notebook = Notebook.objects.get(id=notebook)
            # Create a new Note assoicated with that notebook
            note = Note(file_name=file.name, 
                        file_content=file.read(), 
                        file_type=file.content_type, 
                        owner=owner,
                        notebooks=notebook)
            note.save()
            return HttpResponse("File uploaded successfully")
        except Notebook.DoesNotExist:
            return HttpResponse("Notebook does not exists")
        except:
            return HttpResponse("Bad request")
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
        # Create a new Notebook
        notebook = Notebook(name=notebook, owner=owner)
        # Save the Notebook
        notebook.save()
        # Return a response
        return HttpResponse("Notebook created successfully")
    else:
        return HttpResponse("Notebook creation failed")
    
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
    template = loader.get_template("search/search.html")
    return HttpResponse(template.render())

def search_results(request):
    template = loader.get_template("search/search_results.html")
    if request.method == 'GET' and request.GET.get("search_words"):
        query = request.GET.get("search_words").split()
    if 'notesonly' in request.GET:
        notesonly = True
    else:
        notesonly = False
    if 'spellcheck' in request.GET:
        spellcheck = True
    else:
        spellcheck = False

    if notesonly:
        # load scrubbed vocab for this notebook
        vocab = ml.load_embeddings(os.path.join(settings.BASE_DIR, 'mmapp/src/ML/vocab_scrubbed.pkl'))
    else:
        vocab = None
    # load keyedvectors object for this notebook
    kv = ml.load_kv(os.path.join(settings.BASE_DIR, "mmapp/src/ML/finetuned_embed.kv"))
    
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

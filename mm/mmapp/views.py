from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from django.contrib.auth import authenticate, login
from .models import Note, Notebook, User
from .src.ML import machine_learning as ml
from .src.spacing import spacing_alg as sp
import json
import os
from spellchecker import SpellChecker
from mm.settings import BASE_DIR

# Registration form
# https://studygyaan.com/django/how-to-create-sign-up-registration-view-in-django

# Password reset
# https://learndjango.com/tutorials/django-password-reset-tutorial

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


# https://stackoverflow.com/questions/3222549/how-to-automatically-login-a-user-after-registration-in-django
def register(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect('index')
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
                newUser.save()
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
        notebook = Notebook.objects.get(id=notebook)
        notebook.delete()
        # Return a response
        return HttpResponse("Notebook deleted successfully")


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
        notebooks = request.POST.getlist('notebooks')
        merged_notebook_name = request.POST['merged_notebook_name']
        print("Notebooks: ", notebooks)
        print("Merged notebook name: ", merged_notebook_name)
        # Get the owner from the request
        owner = request.user
        # Create a new Notebook
        notebook = Notebook(name=merged_notebook_name, owner=owner)
        # Save the Notebook
        notebook.save()
        # Return a response
        for n in notebooks:
            n = Notebook.objects.get(id=n)
            notes = Note.objects.filter(notebooks=n)
            for note in notes:
                new_note = Note(file_name=note.file_name, 
                        file_content=note.file_content, 
                        file_type=note.file_type, 
                        owner=owner,
                        notebooks=notebook)
                new_note.save()
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
    template = loader.get_template("search/search.html")
    return HttpResponse(template.render())

def search_results(request):
    template = loader.get_template("search/results.html")
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

    # load scrubbed vocab for this notebook
    print("BASE_DIR", BASE_DIR)
    print(os.path.join(BASE_DIR, 'mmapp\\src\\ML\\vocab_scrubbed.pkl'))
    # TODO: Unable to load vocab_scrubbed.pkl as it doesn't exist
    vocab = ml.load_embeddings(os.path.join(BASE_DIR, 'mmapp\\src\\ML\\vocab_scrubbed.pkl'))
    # load keyedvectors object for this notebook
    print(os.path.join(BASE_DIR, "mmapp\\src\\ML\\finetuned_embed.kv"))
    # TODO: Unable to load finetuned_embed.kv as it doesn't exist
    kv = ml.load_kv(os.path.join(BASE_DIR, "mmapp\\src\\ML\\finetuned_embed.kv"))
    
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
    word_list = []
    for word in words_pos:
        word_list.append({"string":word, "pos":list(words_pos[word])})
    print(word_list)
    # https://stackoverflow.com/questions/43305020/how-to-use-the-context-variables-passed-from-django-in-javascript
    context = {
        "res": res_matrix,
        "words_pos": json.dumps(word_list),
        "spell_checked": spell_checked,
        "skipwords": skipwords
    }
    return render(request, "search/results.html", context)


from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from .models import Note, Notebook
from .src.ML import machine_learning as ml
from .src.spacing import spacing_alg as sp
import os
from spellchecker import SpellChecker

# Create your views here.
def index(request):
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

"""
Receive a file from the user and save it to the database as a Note.
"""
def upload(request):
    if request.method == 'POST':
        # Get the file from the request
        print("request", request)
        print("request.FILES", request.FILES)
        print("request.post", request.POST)
        file = request.FILES['file']
        notebook = request.POST['notebook']
        # Get the notebook from the request
        # notebook = request.POST['notebook']
        # Get the owner from the request
        owner = request.user
        # Create a new Note
        note = Note(file_name=file.name, file_content=file.read(), file_type=file.content_type, owner=owner)
        # Save the Note
        note.save()
        # Get the notebook from the database
        notebook = Notebook.objects.get(id=notebook)
        # Add the note to the notebook
        notebook.notes.add(note)
        # Save the notebook
        notebook.save()
        # Return a response
        return HttpResponse("File uploaded successfully")
    else:
        return HttpResponse("File upload failed")
    
"""
Create a new notebook for the user.
"""
def create_notebook(request):
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
    
def search(request):
    template = loader.get_template("search/search.html")
    return HttpResponse(template.render())

def search_results(request):
    template = loader.get_template("search/search_results.html")
    query = request.GET.get("search_words").split()

    # load scrubbed vocab for this notebook
    vocab = ml.load_embeddings(os.path.join(settings.BASE_DIR, 'mmapp/src/ML/vocab_scrubbed.pkl'))
    # load keyedvectors object for this notebook
    kv = ml.load_kv(os.path.join(settings.BASE_DIR, "mmapp/src/ML/finetuned_embed.kv"))
    
    # spell check
    # TODO: add a spell check toggle so they can override this if they want
    spell = SpellChecker()
    misspelled = spell.unknown(query)
    spell_checked = {}
    for word in misspelled:
        correct_word = spell.correction(word)
        query.remove(word)
        query.append(correct_word)
        spell_checked[word] = correct_word
        print(word)

    # perform search
    res_matrix, words = ml.search(query, kv, 1, vocab)

    # send results to spacing alg
    positions = sp.fruchterman_reingold(res_matrix)
    #print(res)
    #words = [line[0] for line in res]

    # create object of words and positions
    words_pos = {words[i]: positions[i] for i in range(len(words))}
    print(words_pos)
    context = {
        "res": res_matrix,
        "words_pos": words_pos,
        "spell_checked": spell_checked
    }

    return render(request, "search/search_results.html", context)
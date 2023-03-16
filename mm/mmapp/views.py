from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Note, Notebook

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
    
def register(request):
    if request.user.is_authenticated:
        return HttpResponse(status=200, content="Already logged in, can't register!")
    return HttpResponse(status=200, content="This is the URL where we edit notebooks!")

# Placeholder response for now
def edit_notebook(request):
    if not request.user.is_authenticated:
        return HttpResponse(status=200, content="Need to be logged in to edit notebooks!")
        # return redirect('login')
    return HttpResponse(status=200, content="This is the URL where we edit notebooks!")

# Placeholder response for now
def search(request):
    if not request.user.is_authenticated:
        return HttpResponse(status=200, content="Need to be logged in to search notes!")
        # return redirect('login')
    return HttpResponse(status=200, content="This is the URL where we search the notes!")

# Placeholder response for now
def settings(request):
    if not request.user.is_authenticated:
        return HttpResponse(status=200, content="Need to be logged in to access settings!")
        # return redirect('login')
    return HttpResponse(status=200, content="This is the URL where the settings page will be!")
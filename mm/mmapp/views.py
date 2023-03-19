from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Note, Notebook
# from ...ML import machine_learning

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
def search(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return HttpResponse(status=200, content="This is the URL where we search the notes!")

# Placeholder response for now
def settings(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return HttpResponse(status=200, content="This is the URL where the settings page will be!")
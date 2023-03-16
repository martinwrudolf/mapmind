from ..models import Note, Notebook
from django.http import HttpResponse

def search_notebook(request, notebook_id):
    return HttpResponse(status=200, content="Searching notebook with id " + notebook_id)

def inspect_notebook(request, notebook_id):
    return HttpResponse(status=200, content="Inspect notebook with id " + notebook_id)
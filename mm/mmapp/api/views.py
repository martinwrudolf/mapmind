from ..models import Note, Notebook
from django.http import HttpResponse

# Placeholders for now!

def search_notebook(request, notebook_id):
    if not request.user.is_authenticated:
        return HttpResponse(status=200, content="Not allowed to search notebooks with id "+ notebook_id+"!")
    return HttpResponse(status=200, content="Searching notebook with id " + notebook_id)

def inspect_notebook(request, notebook_id):
    if not request.user.is_authenticated:
         return HttpResponse(status=200, content="Not allowed to inspect notebooks with id "+notebook_id+"!")
    return HttpResponse(status=200, content="Inspect notebook with id " + notebook_id)
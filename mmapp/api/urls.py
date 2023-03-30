from django.urls import path
from . import views

urlpatterns = [
    path('search/<str:notebook_id>', views.search_notebook, name='search_notebook'),
    path('inspect/<str:notebook_id>', views.inspect_notebook, name='inspect_notebook')
]
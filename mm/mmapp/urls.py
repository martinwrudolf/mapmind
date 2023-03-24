from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login),
    path('upload', views.upload, name='upload'),
    path('create_notebook', views.create_notebook, name='create_notebook'),
    path('delete_notebook', views.delete_notebook, name='delete_notebook'),
    path('edit_notebook', views.edit_notebook, name='edit_notebook'),
    path('search', views.search, name='search'),
    path('settings', views.settings, name='settings'),
    path('register', views.register, name='register'),
    path('search_results', views.search_results, name='search_results'),
    path('results', views.results, name='results'),
]
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login, name='login_page'),
    path('upload', views.upload, name='upload'),
    path('create_notebook', views.create_notebook, name='create_notebook'),
    path('delete_notebook', views.delete_notebook, name='delete_notebook'),
    path('delete_notes', views.delete_notes, name='delete_notes'),
    path('edit_notebook', views.edit_notebook, name='edit_notebook'),
    path('merge_notebooks', views.merge_notebooks, name='merge_notebooks'),
    path('search', views.search, name='search'),
    path('settings', views.settings, name='settings'),
    path('register', views.register, name='register'),
    path('search_results', views.search_results, name='search_results'),
    path('results', views.results, name='results'),
    path('edit_username', views.edit_username, name='edit_username'),
    path('edit_email', views.edit_email, name='edit_email'),
    path('delete_account', views.delete_account, name='delete_account'),
    path('notebooks', views.notebooks, name='notebooks'),
]
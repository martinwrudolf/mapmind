from django.urls import path, include

from . import views

urlpatterns = [
    path('login', views.login),
    path('upload', views.upload, name='upload'),
    path('create_notebook', views.create_notebook, name='create_notebook'),
    path('delete_notebook', views.delete_notebook, name='delete_notebook'),
    path('delete_notes', views.delete_notes, name='delete_notes'),
    path('edit_notebook', views.edit_notebook, name='edit_notebook'),
    path('merge_notebooks', views.merge_notebooks, name='merge_notebooks'),
    path('settings', views.settings, name='settings'),
    path('register/', views.register, name='register'),
    path('', views.search_results, name='search_results'),
    path('edit_username', views.edit_username, name='edit_username'),
    path('edit_email', views.edit_email, name='edit_email'),
    path('delete_account', views.delete_account, name='delete_account'),
    path('notebooks', views.notebooks, name='notebooks'),
    path('inspect_node', views.inspect_node, name='inspect_node')
]
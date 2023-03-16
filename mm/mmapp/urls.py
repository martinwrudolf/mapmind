from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload', views.upload, name='upload'),
    path('create_notebook', views.create_notebook, name='create_notebook'),
    path('edit_notebook', views.edit_notebook, name='edit_notebook'),
    path('search', views.search, name='search'),
    path('settings', views.settings, name='settings'),
]
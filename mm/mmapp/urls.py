from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload', views.upload, name='upload'),
    path('create_notebook', views.create_notebook, name='create_notebook'),
]
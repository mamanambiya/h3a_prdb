from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path("<str:funder>", views.index, name="FunderProjects"),
    path("projects/<int:pid>", views.projectdetail, name="ProjectDetail"),
]

from django.urls import path
from .views import ProjectListCreateView, ProjectDetailView, MyProjectsView

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='project-list-create'),
    path('my/', MyProjectsView.as_view(), name='my-projects'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
]

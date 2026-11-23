from django.urls import path
from .views import (
    ProjectListCreateView,
    ProjectDetailView,
    MyProjectsView,
    ExploreProjectsView,
    ProjectMembersListView,
    ProjectMemberDetailView,
)

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='project-list-create'),
    path('my/', MyProjectsView.as_view(), name='my-projects'),
    path('explore/', ExploreProjectsView.as_view(), name='project-explore'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/members/', ProjectMembersListView.as_view(), name='project-members'),
    path('<int:pk>/members/<int:user_id>/', ProjectMemberDetailView.as_view(), name='project-member-detail'),
]

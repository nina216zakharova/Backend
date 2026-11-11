from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from .models import Project
from django.db import models
from .serializers import ProjectSerializer,  MyProjectsSerializer

from rest_framework.filters import SearchFilter


class ProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.filter(status=Project.STATUS_OPEN)
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = [SearchFilter]
    search_fields = ['title']

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]



class MyProjectsView(generics.ListAPIView):
    serializer_class = MyProjectsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return Project.objects.filter(
            models.Q(creator=user) | models.Q(members__user=user)
        ).distinct()


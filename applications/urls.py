from django.urls import path
from .views import (
    MembershipRequestListCreateView,
    MembershipRequestDetailView,
    MembershipStatsView,
)

app_name = 'applications'

urlpatterns = [
    path('requests/', MembershipRequestListCreateView.as_view(), name='request-list-create'),
    path('requests/stats/', MembershipStatsView.as_view(), name='request-stats'),
    path('requests/<int:pk>/', MembershipRequestDetailView.as_view(), name='request-detail'),
]

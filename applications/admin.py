from django.contrib import admin
from .models import MembershipRequest


@admin.register(MembershipRequest)
class MembershipRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'user', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('project__title', 'user__username', 'user__email', 'message')
    readonly_fields = ('created_at', 'updated_at')

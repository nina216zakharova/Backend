from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import GoogleProfile

User = get_user_model()


class GoogleProfileInline(admin.StackedInline):
    model = GoogleProfile
    can_delete = False
    verbose_name_plural = "Google Profile"
    readonly_fields = ("google_id", "picture", "created_at", "updated_at")
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = (GoogleProfileInline,)


if admin.site.is_registered(User):
    admin.site.unregister(User)

admin.site.register(User, UserAdmin)
admin.site.register(GoogleProfile)

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import GoogleProfile, Profile

User = get_user_model()


class GoogleProfileInline(admin.StackedInline):
    model = GoogleProfile
    can_delete = False
    verbose_name_plural = "Google Profile"
    readonly_fields = ("google_id", "picture", "created_at", "updated_at")
    extra = 0


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "User Profile"
    filter_horizontal = ('skills',)
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, GoogleProfileInline)


if admin.site.is_registered(User):
    admin.site.unregister(User)

admin.site.register(User, UserAdmin)
admin.site.register(GoogleProfile)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'headline', 'open_to_collaboration', 'open_to_mentoring', 'created_at')
    list_filter = ('open_to_collaboration', 'open_to_mentoring', 'created_at')
    search_fields = ('user__username', 'user__email', 'name', 'headline', 'bio')
    filter_horizontal = ('skills',)

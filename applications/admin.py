from django.contrib import admin, messages
from django.db import transaction
from .models import MembershipRequest
from projects.models import Project, ProjectMember


@admin.register(MembershipRequest)
class MembershipRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'user', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'project')
    search_fields = ('project__title', 'user__username', 'user__email', 'message', 'response_message')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_selected_requests', 'reject_selected_requests']

    @admin.action(description="Approve selected pending requests")
    def approve_selected_requests(self, request, queryset):
        approved = 0
        skipped = 0
        for req in queryset:
            if req.status != MembershipRequest.STATUS_PENDING:
                skipped += 1
                continue

            with transaction.atomic():
                project = Project.objects.select_for_update().get(pk=req.project_id)
                if project.members.count() >= project.capacity:
                    skipped += 1
                    continue

                req.status = MembershipRequest.STATUS_ACCEPTED
                req.save(update_fields=['status', 'updated_at'])
                ProjectMember.objects.get_or_create(project=project, user=req.user)

                if project.members.count() >= project.capacity:
                    project.status = Project.STATUS_CLOSED
                    project.save(update_fields=['status', 'updated_at'])

                approved += 1

        self.message_user(
            request,
            f"{approved} requests approved successfully ({skipped} skipped).",
            messages.SUCCESS,
        )

    @admin.action(description="Reject selected pending requests")
    def reject_selected_requests(self, request, queryset):
        updated = queryset.filter(status=MembershipRequest.STATUS_PENDING).update(
            status=MembershipRequest.STATUS_REJECTED
        )
        self.message_user(
            request,
            f"{updated} requests marked as rejected.",
            messages.INFO,
        )

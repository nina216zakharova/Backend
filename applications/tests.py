from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from applications.models import MembershipRequest
from projects.models import Project, ProjectMember

User = get_user_model()


class MembershipRequestTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="project_creator",
            email="creator@example.com",
            password="password123",
        )
        self.applicant = User.objects.create_user(
            username="applicant_user",
            email="applicant@example.com",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            username="random_user",
            email="random@example.com",
            password="password123",
        )

        self.project = Project.objects.create(
            title="AI Collaboration Platform",
            goal="Build a platform for university students",
            description="Matching students with projects",
            creator=self.creator,
            capacity=2,
            status=Project.STATUS_OPEN,
        )

        self.creator_token = Token.objects.create(user=self.creator)
        self.applicant_token = Token.objects.create(user=self.applicant)
        self.other_token = Token.objects.create(user=self.other_user)

        self.client = APIClient()

    def test_submit_membership_request_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.applicant_token.key}")
        payload = {
            "project": self.project.id,
            "message": "I would love to contribute with Python and Django.",
        }
        response = self.client.post("/api/applications/requests/", payload, format="json")

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["project"], self.project.id)
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["applicant_username"], "applicant_user")
        self.assertTrue(MembershipRequest.objects.filter(project=self.project, user=self.applicant).exists())

    def test_creator_cannot_apply_to_own_project(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.creator_token.key}")
        payload = {"project": self.project.id, "message": "Applying to my own project"}
        response = self.client.post("/api/applications/requests/", payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("You cannot apply to your own project.", str(response.json()))

    def test_cannot_apply_to_closed_project(self):
        self.project.status = Project.STATUS_CLOSED
        self.project.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.applicant_token.key}")
        payload = {"project": self.project.id, "message": "Applying to closed project"}
        response = self.client.post("/api/applications/requests/", payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Cannot apply to a closed project.", str(response.json()))

    def test_cannot_apply_if_already_member(self):
        ProjectMember.objects.create(project=self.project, user=self.applicant)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.applicant_token.key}")
        payload = {"project": self.project.id, "message": "Applying again"}
        response = self.client.post("/api/applications/requests/", payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("You are already a member of this project.", str(response.json()))

    def test_cannot_submit_duplicate_pending_request(self):
        MembershipRequest.objects.create(
            project=self.project,
            user=self.applicant,
            status=MembershipRequest.STATUS_PENDING,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.applicant_token.key}")
        payload = {"project": self.project.id, "message": "Second request"}
        response = self.client.post("/api/applications/requests/", payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("You already have a pending request for this project.", str(response.json()))

    def test_cannot_apply_when_capacity_full(self):
        self.project.capacity = 1
        self.project.save()
        ProjectMember.objects.create(project=self.project, user=self.other_user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.applicant_token.key}")
        payload = {"project": self.project.id, "message": "Applying to full project"}
        response = self.client.post("/api/applications/requests/", payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Project team capacity is already full.", str(response.json()))

    def test_creator_can_accept_request_with_response_message(self):
        req = MembershipRequest.objects.create(
            project=self.project,
            user=self.applicant,
            message="Please accept me",
            status=MembershipRequest.STATUS_PENDING,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.creator_token.key}")
        response = self.client.patch(
            f"/api/applications/requests/{req.id}/",
            {"status": "accepted", "response_message": "Welcome to our engineering team!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        req.refresh_from_db()
        self.assertEqual(req.status, MembershipRequest.STATUS_ACCEPTED)
        self.assertEqual(req.response_message, "Welcome to our engineering team!")
        self.assertTrue(ProjectMember.objects.filter(project=self.project, user=self.applicant).exists())

    def test_creator_can_reject_request_with_response_message(self):
        req = MembershipRequest.objects.create(
            project=self.project,
            user=self.applicant,
            message="Please accept me",
            status=MembershipRequest.STATUS_PENDING,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.creator_token.key}")
        response = self.client.patch(
            f"/api/applications/requests/{req.id}/",
            {"status": "rejected", "response_message": "Currently looking for senior members."},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        req.refresh_from_db()
        self.assertEqual(req.status, MembershipRequest.STATUS_REJECTED)
        self.assertEqual(req.response_message, "Currently looking for senior members.")
        self.assertFalse(ProjectMember.objects.filter(project=self.project, user=self.applicant).exists())

    def test_project_automatically_closes_when_capacity_reached(self):
        self.project.capacity = 1
        self.project.save()

        req = MembershipRequest.objects.create(
            project=self.project,
            user=self.applicant,
            status=MembershipRequest.STATUS_PENDING,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.creator_token.key}")
        response = self.client.patch(
            f"/api/applications/requests/{req.id}/",
            {"status": "accepted"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.STATUS_CLOSED)

    def test_applicant_cannot_accept_own_request(self):
        req = MembershipRequest.objects.create(
            project=self.project,
            user=self.applicant,
            status=MembershipRequest.STATUS_PENDING,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.applicant_token.key}")
        response = self.client.patch(
            f"/api/applications/requests/{req.id}/",
            {"status": "accepted"},
            format="json",
        )

        self.assertIn(response.status_code, [400, 403])

    def test_cannot_update_already_finalized_request(self):
        req = MembershipRequest.objects.create(
            project=self.project,
            user=self.applicant,
            status=MembershipRequest.STATUS_ACCEPTED,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.creator_token.key}")
        response = self.client.patch(
            f"/api/applications/requests/{req.id}/",
            {"status": "rejected"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_applicant_can_withdraw_pending_request(self):
        req = MembershipRequest.objects.create(
            project=self.project,
            user=self.applicant,
            status=MembershipRequest.STATUS_PENDING,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.applicant_token.key}")
        response = self.client.delete(f"/api/applications/requests/{req.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(MembershipRequest.objects.filter(id=req.id).exists())

    def test_applicant_cannot_withdraw_accepted_request(self):
        req = MembershipRequest.objects.create(
            project=self.project,
            user=self.applicant,
            status=MembershipRequest.STATUS_ACCEPTED,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.applicant_token.key}")
        response = self.client.delete(f"/api/applications/requests/{req.id}/")

        self.assertEqual(response.status_code, 400)
        self.assertTrue(MembershipRequest.objects.filter(id=req.id).exists())

    def test_creator_cannot_delete_request(self):
        req = MembershipRequest.objects.create(
            project=self.project,
            user=self.applicant,
            status=MembershipRequest.STATUS_PENDING,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.creator_token.key}")
        response = self.client.delete(f"/api/applications/requests/{req.id}/")

        self.assertEqual(response.status_code, 403)

    def test_membership_stats_endpoint(self):
        MembershipRequest.objects.create(
            project=self.project,
            user=self.applicant,
            status=MembershipRequest.STATUS_PENDING,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.creator_token.key}")
        response = self.client.get("/api/applications/requests/stats/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("sent", data)
        self.assertIn("received", data)
        self.assertEqual(data["received"]["pending"], 1)

    def test_list_requests_search_and_ordering(self):
        MembershipRequest.objects.create(
            project=self.project,
            user=self.applicant,
            message="Unique searchable note",
            status=MembershipRequest.STATUS_PENDING,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.applicant_token.key}")
        response = self.client.get("/api/applications/requests/?search=searchable")

        self.assertEqual(response.status_code, 200)
        results = response.json().get("results", response.json())
        self.assertEqual(len(results), 1)

    def test_creator_can_remove_project_member_and_reopen_project(self):
        self.project.capacity = 1
        self.project.status = Project.STATUS_CLOSED
        self.project.save()

        member = ProjectMember.objects.create(project=self.project, user=self.applicant)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.creator_token.key}")
        response = self.client.delete(f"/api/projects/{self.project.id}/members/{self.applicant.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProjectMember.objects.filter(id=member.id).exists())

        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.STATUS_OPEN)

    def test_member_can_voluntarily_leave_project(self):
        member = ProjectMember.objects.create(project=self.project, user=self.applicant)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.applicant_token.key}")
        response = self.client.delete(f"/api/projects/{self.project.id}/members/{self.applicant.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProjectMember.objects.filter(id=member.id).exists())

    def test_unauthorized_user_cannot_remove_member(self):
        ProjectMember.objects.create(project=self.project, user=self.applicant)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.other_token.key}")
        response = self.client.delete(f"/api/projects/{self.project.id}/members/{self.applicant.id}/")

        self.assertEqual(response.status_code, 403)

    def test_project_members_list_view(self):
        ProjectMember.objects.create(project=self.project, user=self.applicant)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.applicant_token.key}")
        response = self.client.get(f"/api/projects/{self.project.id}/members/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["user"]["username"], "applicant_user")

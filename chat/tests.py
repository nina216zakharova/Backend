from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from projects.models import Project
from chat.models import Conversation, Message

User = get_user_model()


class ChatAPITests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="alice", email="alice@example.com", password="password123")
        self.user2 = User.objects.create_user(username="bob", email="bob@example.com", password="password123")
        self.user3 = User.objects.create_user(username="charlie", email="charlie@example.com", password="password123")

        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
        self.token3 = Token.objects.create(user=self.user3)

        self.auth_headers1 = {"HTTP_AUTHORIZATION": f"Token {self.token1.key}"}
        self.auth_headers2 = {"HTTP_AUTHORIZATION": f"Token {self.token2.key}"}
        self.auth_headers3 = {"HTTP_AUTHORIZATION": f"Token {self.token3.key}"}

        self.project = Project.objects.create(
            title="AI Collaboration Engine",
            goal="Developing multi-agent chat tools.",
            description="Developing multi-agent chat tools.",
            creator=self.user1,
            capacity=5,
        )

    def test_start_conversation_success(self):
        payload = {
            "recipient_id": self.user2.id,
            "project_id": self.project.id,
        }
        response = self.client.post(
            "/api/chat/conversations/",
            payload,
            content_type="application/json",
            **self.auth_headers1,
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["other_participant"]["username"], "bob")
        self.assertEqual(data["project"]["title"], "AI Collaboration Engine")

        # Starting again returns the same existing conversation
        response2 = self.client.post(
            "/api/chat/conversations/",
            payload,
            content_type="application/json",
            **self.auth_headers1,
        )
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json()["id"], data["id"])

    def test_list_conversations(self):
        conv = Conversation.objects.create(project=self.project)
        conv.participants.add(self.user1, self.user2)
        Message.objects.create(conversation=conv, sender=self.user2, content="سلام آلیس!")

        response = self.client.get("/api/chat/conversations/", **self.auth_headers1)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["last_message"]["content"], "سلام آلیس!")
        self.assertEqual(data[0]["unread_count"], 1)

    def test_send_and_read_messages(self):
        conv = Conversation.objects.create(project=self.project)
        conv.participants.add(self.user1, self.user2)

        # Alice sends a message to Bob
        payload = {"content": "سلام باب، آیا به همکاری علاقه‌مندی؟"}
        send_res = self.client.post(
            f"/api/chat/conversations/{conv.id}/messages/",
            payload,
            content_type="application/json",
            **self.auth_headers1,
        )
        self.assertEqual(send_res.status_code, 201)
        self.assertEqual(send_res.json()["content"], "سلام باب، آیا به همکاری علاقه‌مندی؟")
        self.assertTrue(send_res.json()["is_mine"])

        # Bob checks unread count: should be 1
        unread_res = self.client.get("/api/chat/unread-count/", **self.auth_headers2)
        self.assertEqual(unread_res.json()["unread_count"], 1)

        # Bob reads the conversation messages
        msg_list_res = self.client.get(
            f"/api/chat/conversations/{conv.id}/messages/",
            **self.auth_headers2,
        )
        self.assertEqual(msg_list_res.status_code, 200)
        self.assertEqual(len(msg_list_res.json()), 1)
        self.assertFalse(msg_list_res.json()[0]["is_mine"])

        # Unread count should now be 0
        unread_after = self.client.get("/api/chat/unread-count/", **self.auth_headers2)
        self.assertEqual(unread_after.json()["unread_count"], 0)

    def test_unauthorized_user_cannot_access_other_conversations(self):
        conv = Conversation.objects.create()
        conv.participants.add(self.user1, self.user2)

        # Charlie (user 3) attempts to read or post to Alice & Bob's conversation
        res = self.client.get(
            f"/api/chat/conversations/{conv.id}/messages/",
            **self.auth_headers3,
        )
        self.assertEqual(res.status_code, 404)

        post_res = self.client.post(
            f"/api/chat/conversations/{conv.id}/messages/",
            {"content": "I am eavesdropping!"},
            content_type="application/json",
            **self.auth_headers3,
        )
        self.assertEqual(post_res.status_code, 404)

    def test_unauthenticated_request_fails(self):
        response = self.client.get("/api/chat/conversations/")
        self.assertEqual(response.status_code, 401)

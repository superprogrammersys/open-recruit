from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from api.models import User, Job, Application
from rest_framework_simplejwt.tokens import RefreshToken


def get_jwt_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


class AuthTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="manager1", password="pass123", role="manager"
        )
        self.recruiter = User.objects.create_user(
            username="recruiter1", password="pass123", role="recruiter"
        )

    def test_jwt_token_obtain(self):
        url = reverse("token_obtain_pair")
        resp = self.client.post(url, {"username": "manager1", "password": "pass123"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_jwt_token_protected(self):
        url = reverse("user-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        token = get_jwt_for_user(self.manager)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class PermissionTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="manager1", password="pass123", role="manager"
        )
        self.recruiter = User.objects.create_user(
            username="recruiter1", password="pass123", role="recruiter"
        )
        self.job = Job.objects.create(
            title="Backend Dev", company="TestCorp", created_by=self.manager
        )
        self.application = Application.objects.create(
            job=self.job, candidate_full_name="Alice", added_by=self.recruiter
        )

    def test_user_permissions(self):
        url = reverse("user-list")
        token = get_jwt_for_user(self.recruiter)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        token = get_jwt_for_user(self.manager)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_job_permissions(self):
        url = reverse("job-list")
        token = get_jwt_for_user(self.recruiter)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        token = get_jwt_for_user(self.manager)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_application_permissions(self):
        url = reverse("application-list")
        token = get_jwt_for_user(self.recruiter)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        token = get_jwt_for_user(self.manager)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class CRUDTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="manager1", password="pass123", role="manager"
        )
        self.recruiter = User.objects.create_user(
            username="recruiter1", password="pass123", role="recruiter"
        )
        self.job = Job.objects.create(
            title="Backend Dev", company="TestCorp", created_by=self.manager
        )

    def test_create_application(self):
        url = reverse("application-list")
        token = get_jwt_for_user(self.recruiter)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        data = {"job": self.job.id, "candidate_full_name": "Bob"}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.count(), 1)
        self.assertEqual(Application.objects.first().candidate_full_name, "Bob")

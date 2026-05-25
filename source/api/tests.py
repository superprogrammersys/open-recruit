from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from api.models import User, Job, Application
from api.queries import (
    get_all_users,
    get_users_by_role,
    get_open_jobs,
    get_closed_jobs,
    get_applications_for_job,
    get_applications_by_stage,
    get_all_applications,
)
from api.serializers import UserSerializer, JobSerializer, ApplicationSerializer
from rest_framework_simplejwt.tokens import RefreshToken
import time


def get_jwt_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


class ModelTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr", password="pass123", role="manager", email="mgr@test.com"
        )
        self.recruiter = User.objects.create_user(
            username="rec", password="pass123", role="recruiter", email="rec@test.com"
        )
        self.job = Job.objects.create(
            title="Python Dev",
            company="TechCo",
            description="Remote position",
            is_open=True,
            job_type="Full-time",
            created_by=self.manager,
        )
        self.application = Application.objects.create(
            job=self.job,
            candidate_full_name="John Doe",
            stage="new",
            added_by=self.recruiter,
        )

    def test_user_str(self):
        self.assertEqual(str(self.manager), "mgr")

    def test_user_role_choices(self):
        self.assertEqual(self.manager.role, "manager")
        self.assertEqual(self.recruiter.role, "recruiter")

    def test_job_str(self):
        expected = "Python Dev at TechCo  (Full-time)"
        self.assertEqual(str(self.job), expected)

    def test_job_defaults(self):
        job = Job.objects.create(title="Test", company="TestCo", created_by=self.manager)
        self.assertTrue(job.is_open)
        self.assertEqual(job.job_type, "Full-time")

    def test_application_str(self):
        expected = "John Doe - Python Dev"
        self.assertEqual(str(self.application), expected)

    def test_application_defaults(self):
        app = Application.objects.create(
            job=self.job, candidate_full_name="Jane", added_by=self.recruiter
        )
        self.assertEqual(app.stage, "new")

    def test_unique_constraint(self):
        with self.assertRaises(Exception):
            Application.objects.create(
                job=self.job, candidate_full_name="John Doe", added_by=self.recruiter
            )

    def test_foreign_key_cascade(self):
        job_id = self.job.id
        self.job.delete()
        self.assertEqual(Application.objects.filter(job_id=job_id).count(), 0)

    def test_user_created_jobs_related_name(self):
        jobs = self.manager.created_jobs.all()
        self.assertEqual(jobs.count(), 1)
        self.assertEqual(jobs.first().title, "Python Dev")


class SerializerTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr", password="pass123", role="manager", email="mgr@test.com"
        )
        self.recruiter = User.objects.create_user(
            username="rec", password="pass123", role="recruiter", email="rec@test.com"
        )
        self.job = Job.objects.create(
            title="DevOps", company="CloudCo", created_by=self.manager
        )

    def test_user_serializer_fields(self):
        serializer = UserSerializer(self.manager)
        data = serializer.data
        self.assertIn("id", data)
        self.assertIn("username", data)
        self.assertIn("email", data)
        self.assertIn("role", data)
        self.assertIn("first_name", data)
        self.assertIn("last_name", data)
        self.assertIn("is_active", data)
        self.assertIn("is_superuser", data)
        self.assertIn("is_staff", data)
        self.assertIn("last_login", data)
        self.assertIn("date_joined", data)
        self.assertNotIn("password", data)

    def test_user_serializer_read_only_fields(self):
        data = {"username": "newuser", "password": "pass123", "role": "recruiter"}
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_user_serializer_validate_email_duplicate(self):
        data = {
            "username": "newuser",
            "password": "pass123",
            "role": "recruiter",
            "email": "mgr@test.com",
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_user_serializer_validate_role_invalid(self):
        data = {"username": "newuser", "password": "pass123", "role": "admin"}
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("role", serializer.errors)

    def test_user_serializer_password_write_only(self):
        serializer = UserSerializer(self.manager)
        self.assertNotIn("password", serializer.data)

    def test_job_serializer_fields(self):
        serializer = JobSerializer(self.job)
        data = serializer.data
        self.assertIn("id", data)
        self.assertIn("title", data)
        self.assertIn("company", data)
        self.assertIn("description", data)
        self.assertIn("is_open", data)
        self.assertIn("job_type", data)
        self.assertIn("created_by", data)
        self.assertIn("created_at", data)

    def test_job_serializer_read_only_fields(self):
        data = {"title": "New Job", "company": "TestCo", "job_type": "Full-time"}
        serializer = JobSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_job_serializer_validate_title_empty(self):
        data = {"title": "   ", "company": "TestCo"}
        serializer = JobSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)

    def test_job_serializer_validate_company_empty(self):
        data = {"title": "Dev", "company": ""}
        serializer = JobSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("company", serializer.errors)

    def test_job_serializer_validate_job_type_invalid(self):
        data = {"title": "Dev", "company": "TestCo", "job_type": "Remote"}
        serializer = JobSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("job_type", serializer.errors)

    def test_application_serializer_fields(self):
        app = Application.objects.create(
            job=self.job, candidate_full_name="Alice", added_by=self.recruiter
        )
        serializer = ApplicationSerializer(app)
        data = serializer.data
        self.assertIn("id", data)
        self.assertIn("job", data)
        self.assertIn("candidate_full_name", data)
        self.assertIn("stage", data)
        self.assertIn("added_by", data)
        self.assertIn("notes", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_application_serializer_validate_name_empty(self):
        data = {"job": self.job.id, "candidate_full_name": "   "}
        serializer = ApplicationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("candidate_full_name", serializer.errors)

    def test_application_serializer_validate_name_short(self):
        data = {"job": self.job.id, "candidate_full_name": "AB"}
        serializer = ApplicationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("candidate_full_name", serializer.errors)

    def test_application_serializer_validate_stage_invalid(self):
        data = {"job": self.job.id, "candidate_full_name": "Alice", "stage": "pending"}
        serializer = ApplicationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("stage", serializer.errors)

    def test_application_serializer_duplicate_validation(self):
        Application.objects.create(
            job=self.job, candidate_full_name="Bob", added_by=self.recruiter
        )
        data = {"job": self.job.id, "candidate_full_name": "Bob"}
        serializer = ApplicationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("candidate_full_name", serializer.errors)

    def test_application_serializer_update_bypasses_duplicate(self):
        app = Application.objects.create(
            job=self.job, candidate_full_name="Eve", added_by=self.recruiter
        )
        data = {"stage": "interview"}
        serializer = ApplicationSerializer(app, data=data, partial=True)
        self.assertTrue(serializer.is_valid())


class QueryTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr", password="pass123", role="manager", email="mgr@test.com"
        )
        self.recruiter = User.objects.create_user(
            username="rec", password="pass123", role="recruiter", email="rec@test.com"
        )
        self.open_job = Job.objects.create(
            title="Open Job", company="OpenCo", is_open=True, created_by=self.manager
        )
        self.closed_job = Job.objects.create(
            title="Closed Job", company="ClosedCo", is_open=False, created_by=self.manager
        )
        self.app1 = Application.objects.create(
            job=self.open_job,
            candidate_full_name="Alice",
            stage="new",
            added_by=self.recruiter,
        )
        self.app2 = Application.objects.create(
            job=self.open_job,
            candidate_full_name="Bob",
            stage="interview",
            added_by=self.recruiter,
        )

    def test_get_all_users(self):
        users = get_all_users()
        self.assertEqual(users.count(), 2)

    def test_get_users_by_role(self):
        managers = get_users_by_role("manager")
        recruiters = get_users_by_role("recruiter")
        self.assertEqual(managers.count(), 1)
        self.assertEqual(recruiters.count(), 1)

    def test_get_users_by_role_empty(self):
        admins = get_users_by_role("admin")
        self.assertEqual(admins.count(), 0)

    def test_get_open_jobs(self):
        jobs = get_open_jobs()
        self.assertEqual(jobs.count(), 1)
        self.assertEqual(jobs.first().title, "Open Job")

    def test_get_closed_jobs(self):
        jobs = get_closed_jobs()
        self.assertEqual(jobs.count(), 1)
        self.assertEqual(jobs.first().title, "Closed Job")

    def test_get_applications_for_job(self):
        apps = get_applications_for_job(self.open_job.id)
        self.assertEqual(apps.count(), 2)

    def test_get_applications_for_job_empty(self):
        apps = get_applications_for_job(9999)
        self.assertEqual(apps.count(), 0)

    def test_get_applications_by_stage(self):
        new_apps = get_applications_by_stage("new")
        interview_apps = get_applications_by_stage("interview")
        self.assertEqual(new_apps.count(), 1)
        self.assertEqual(interview_apps.count(), 1)
        self.assertEqual(new_apps.first().candidate_full_name, "Alice")

    def test_get_applications_by_stage_empty(self):
        hired_apps = get_applications_by_stage("hired")
        self.assertEqual(hired_apps.count(), 0)

    def test_get_all_applications(self):
        apps = get_all_applications()
        self.assertEqual(apps.count(), 2)

    def test_select_related_open_jobs(self):
        jobs = get_open_jobs()
        job = jobs.first()
        self.assertEqual(job.created_by.username, "mgr")

    def test_select_related_applications(self):
        apps = get_all_applications()
        app = apps.first()
        self.assertEqual(app.added_by.username, "rec")
        self.assertEqual(app.job.title, "Open Job")


class AuthEndpointTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr", password="pass123", role="manager", email="mgr@test.com"
        )

    def test_token_obtain_valid(self):
        url = reverse("token_obtain_pair")
        resp = self.client.post(url, {"username": "mgr", "password": "pass123"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_token_obtain_invalid_password(self):
        url = reverse("token_obtain_pair")
        resp = self.client.post(url, {"username": "mgr", "password": "wrong"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_obtain_invalid_username(self):
        url = reverse("token_obtain_pair")
        resp = self.client.post(url, {"username": "ghost", "password": "pass123"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_obtain_empty_fields(self):
        url = reverse("token_obtain_pair")
        resp = self.client.post(url, {"username": "", "password": ""})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_refresh_valid(self):
        refresh = RefreshToken.for_user(self.manager)
        url = reverse("token_refresh")
        resp = self.client.post(url, {"refresh": str(refresh)})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)

    def test_token_refresh_invalid(self):
        url = reverse("token_refresh")
        resp = self.client.post(url, {"refresh": "invalidtoken"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class UserEndpointTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr", password="pass123", role="manager", email="mgr@test.com"
        )
        self.recruiter = User.objects.create_user(
            username="rec", password="pass123", role="recruiter", email="rec@test.com"
        )
        self.manager_token = get_jwt_for_user(self.manager)
        self.recruiter_token = get_jwt_for_user(self.recruiter)

    def test_list_users_as_manager(self):
        url = reverse("user-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)
        self.assertEqual(len(resp.data["results"]), 2)

    def test_list_users_as_recruiter(self):
        url = reverse("user-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_users_unauthenticated(self):
        url = reverse("user-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_as_manager(self):
        url = reverse("user-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        data = {
            "username": "newuser",
            "password": "newpass123",
            "role": "recruiter",
            "email": "new@test.com",
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)

    def test_create_user_as_recruiter(self):
        url = reverse("user-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        data = {
            "username": "newuser",
            "password": "newpass123",
            "role": "recruiter",
            "email": "new@test.com",
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_user_duplicate_email(self):
        url = reverse("user-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        data = {
            "username": "newuser",
            "password": "newpass123",
            "role": "recruiter",
            "email": "mgr@test.com",
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_invalid_role(self):
        url = reverse("user-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        data = {
            "username": "newuser",
            "password": "newpass123",
            "role": "admin",
            "email": "new@test.com",
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_missing_fields(self):
        url = reverse("user-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        data = {"username": "newuser"}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_as_manager(self):
        url = reverse("user-detail", kwargs={"pk": self.recruiter.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "rec")

    def test_retrieve_user_as_recruiter(self):
        url = reverse("user-detail", kwargs={"pk": self.manager.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_as_manager(self):
        url = reverse("user-detail", kwargs={"pk": self.recruiter.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        data = {"first_name": "Updated"}
        resp = self.client.patch(url, data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.recruiter.refresh_from_db()
        self.assertEqual(self.recruiter.first_name, "Updated")

    def test_update_user_as_recruiter(self):
        url = reverse("user-detail", kwargs={"pk": self.recruiter.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        data = {"first_name": "Hacked"}
        resp = self.client.patch(url, data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_user_as_manager(self):
        url = reverse("user-detail", kwargs={"pk": self.recruiter.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 1)

    def test_delete_user_as_recruiter(self):
        url = reverse("user-detail", kwargs={"pk": self.manager.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_password_not_in_response(self):
        url = reverse("user-detail", kwargs={"pk": self.manager.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        resp = self.client.get(url)
        self.assertNotIn("password", resp.data)

    def test_user_cannot_set_is_superuser(self):
        url = reverse("user-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        data = {
            "username": "hacker",
            "password": "pass123",
            "role": "recruiter",
            "email": "hacker@test.com",
            "is_superuser": True,
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="hacker")
        self.assertFalse(user.is_superuser)


class JobEndpointTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr", password="pass123", role="manager", email="mgr@test.com"
        )
        self.recruiter = User.objects.create_user(
            username="rec", password="pass123", role="recruiter", email="rec@test.com"
        )
        self.job = Job.objects.create(
            title="DevOps", company="CloudCo", created_by=self.manager
        )
        self.manager_token = get_jwt_for_user(self.manager)
        self.recruiter_token = get_jwt_for_user(self.recruiter)

    def test_list_jobs_as_manager(self):
        url = reverse("job-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_jobs_as_recruiter(self):
        url = reverse("job-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_jobs_unauthenticated(self):
        url = reverse("job-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_job_as_manager(self):
        url = reverse("job-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        data = {"title": "New Job", "company": "NewCo", "job_type": "Part-time"}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Job.objects.count(), 2)

    def test_create_job_as_recruiter(self):
        url = reverse("job-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        data = {"title": "New Job", "company": "NewCo", "job_type": "Part-time"}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_job_empty_title(self):
        url = reverse("job-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        data = {"title": "   ", "company": "NewCo"}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_job_invalid_type(self):
        url = reverse("job-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        data = {"title": "Dev", "company": "NewCo", "job_type": "Remote"}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_job(self):
        url = reverse("job-detail", kwargs={"pk": self.job.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["title"], "DevOps")

    def test_update_job_as_manager(self):
        url = reverse("job-detail", kwargs={"pk": self.job.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        data = {"title": "Updated DevOps"}
        resp = self.client.patch(url, data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, "Updated DevOps")

    def test_update_job_as_recruiter(self):
        url = reverse("job-detail", kwargs={"pk": self.job.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        data = {"title": "Hacked"}
        resp = self.client.patch(url, data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_job_as_manager(self):
        url = reverse("job-detail", kwargs={"pk": self.job.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Job.objects.count(), 0)

    def test_delete_job_as_recruiter(self):
        url = reverse("job-detail", kwargs={"pk": self.job.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_job_created_by_is_read_only(self):
        url = reverse("job-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        data = {
            "title": "Test",
            "company": "TestCo",
            "job_type": "Full-time",
            "created_by": self.recruiter.pk,
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        job = Job.objects.get(title="Test")
        self.assertIsNone(job.created_by)


class ApplicationEndpointTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr", password="pass123", role="manager", email="mgr@test.com"
        )
        self.recruiter = User.objects.create_user(
            username="rec", password="pass123", role="recruiter", email="rec@test.com"
        )
        self.job = Job.objects.create(
            title="DevOps", company="CloudCo", created_by=self.manager
        )
        self.application = Application.objects.create(
            job=self.job,
            candidate_full_name="Alice",
            stage="new",
            added_by=self.recruiter,
        )
        self.manager_token = get_jwt_for_user(self.manager)
        self.recruiter_token = get_jwt_for_user(self.recruiter)

    def test_list_applications_as_recruiter(self):
        url = reverse("application-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_applications_as_manager(self):
        url = reverse("application-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_applications_unauthenticated(self):
        url = reverse("application-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filter_applications_by_stage(self):
        Application.objects.create(
            job=self.job,
            candidate_full_name="Bob",
            stage="interview",
            added_by=self.recruiter,
        )
        url = reverse("application-list") + "?stage=new"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["candidate_full_name"], "Alice")

    def test_create_application_as_recruiter(self):
        url = reverse("application-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        data = {"job": self.job.pk, "candidate_full_name": "Charlie"}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.count(), 2)

    def test_create_application_as_manager(self):
        url = reverse("application-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        data = {"job": self.job.pk, "candidate_full_name": "Charlie"}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_application_duplicate(self):
        url = reverse("application-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        data = {"job": self.job.pk, "candidate_full_name": "Alice"}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_application_empty_name(self):
        url = reverse("application-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        data = {"job": self.job.pk, "candidate_full_name": "   "}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_application_short_name(self):
        url = reverse("application-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        data = {"job": self.job.pk, "candidate_full_name": "AB"}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_application(self):
        url = reverse("application-detail", kwargs={"pk": self.application.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["candidate_full_name"], "Alice")

    def test_update_application_stage(self):
        url = reverse("application-detail", kwargs={"pk": self.application.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        data = {"stage": "interview"}
        resp = self.client.patch(url, data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.stage, "interview")

    def test_update_application_invalid_stage(self):
        url = reverse("application-detail", kwargs={"pk": self.application.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        data = {"stage": "pending"}
        resp = self.client.patch(url, data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_application_as_recruiter(self):
        url = reverse("application-detail", kwargs={"pk": self.application.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Application.objects.count(), 0)

    def test_delete_application_as_manager(self):
        url = reverse("application-detail", kwargs={"pk": self.application.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.manager_token}")
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_application_added_by_is_read_only(self):
        url = reverse("application-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.recruiter_token}")
        data = {
            "job": self.job.pk,
            "candidate_full_name": "Eve",
            "added_by": self.manager.pk,
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        app = Application.objects.get(candidate_full_name="Eve")
        self.assertIsNone(app.added_by)


class PaginationTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr", password="pass123", role="manager", email="mgr@test.com"
        )
        self.token = get_jwt_for_user(self.manager)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_user_list_pagination_structure(self):
        url = reverse("user-list")
        resp = self.client.get(url)
        self.assertIn("results", resp.data)
        self.assertIn("next", resp.data)
        self.assertIn("previous", resp.data)

    def test_job_list_pagination_structure(self):
        url = reverse("job-list")
        resp = self.client.get(url)
        self.assertIn("results", resp.data)
        self.assertIn("next", resp.data)
        self.assertIn("previous", resp.data)

    def test_application_list_pagination_structure(self):
        url = reverse("application-list")
        resp = self.client.get(url)
        self.assertIn("results", resp.data)
        self.assertIn("next", resp.data)
        self.assertIn("previous", resp.data)

    def test_user_pagination_creates_pages(self):
        for i in range(25):
            User.objects.create_user(
                username=f"user_{i}",
                password="pass123",
                role="recruiter",
                email=f"user_{i}@test.com",
            )
        url = reverse("user-list")
        resp = self.client.get(url)
        self.assertIsNotNone(resp.data["next"])
        self.assertEqual(len(resp.data["results"]), 20)


class PerformanceTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        print("\nCreating 100,000 users...")
        start = time.time()
        
        users = []
        for i in range(100_000):
            users.append(
                User(
                    username=f"perf_user_{i}",
                    email=f"perf_user_{i}@test.com",
                    role="recruiter" if i % 2 == 0 else "manager"
                )
            )
        
        User.objects.bulk_create(users, batch_size=5000)
        
        elapsed = time.time() - start
        print(f"Created 100,000 users in {elapsed:.2f}s")
        
        cls.manager = User.objects.create_user(
            username="admin_mgr",
            password="pass123",
            role="manager",
            email="admin_mgr@test.com"
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.token = get_jwt_for_user(self.manager)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_count_all_users(self):
        start = time.time()
        count = get_all_users().count()
        elapsed = time.time() - start
        
        print(f"\nUser count: {count:,}")
        print(f"Count time: {elapsed:.4f}s")
        
        self.assertEqual(count, 100_001)

    def test_get_all_users_paginated(self):
        url = reverse("user-list")
        
        start = time.time()
        resp = self.client.get(url)
        elapsed = time.time() - start
        
        print(f"\nFirst page ({len(resp.data['results'])} users)")
        print(f"API fetch time: {elapsed:.4f}s")
        
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)
        self.assertIn("next", resp.data)
        self.assertLess(elapsed, 5.0)

    def test_filter_users_by_role(self):
        start = time.time()
        recruiters = get_users_by_role("recruiter")
        managers = get_users_by_role("manager")
        elapsed = time.time() - start
        
        recruiter_count = recruiters.count()
        manager_count = managers.count()
        
        print(f"\nRecruiters: {recruiter_count:,}")
        print(f"Managers: {manager_count:,}")
        print(f"Filter time: {elapsed:.4f}s")
        
        self.assertEqual(recruiter_count, 50_000)
        self.assertEqual(manager_count, 50_001)

    def test_pagination_performance(self):
        url = reverse("user-list")
        total_time = 0
        
        print(f"\nBrowsing 10 pages:")
        for page in range(1, 11):
            start = time.time()
            resp = self.client.get(f"{url}?page={page}")
            elapsed = time.time() - start
            total_time += elapsed
            
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            
            if page <= 3 or page >= 9:
                print(f"  Page {page}: {elapsed:.4f}s ({len(resp.data['results'])} users)")
            elif page == 4:
                print(f"  ... (pages 4-8 hidden) ...")
        
        avg_time = total_time / 10
        print(f"Avg page time: {avg_time:.4f}s")
        print(f"Total time for 10 pages: {total_time:.4f}s")
        
        self.assertLess(avg_time, 2.0)

    def test_email_uniqueness_check(self):
        start = time.time()
        exists = User.objects.filter(email="perf_user_50000@test.com").exists()
        elapsed = time.time() - start
        
        print(f"\nEmail lookup: {elapsed:.4f}s")
        self.assertTrue(exists)
        self.assertLess(elapsed, 0.1)

    def test_search_by_username(self):
        start = time.time()
        user = User.objects.filter(username="perf_user_99999").first()
        elapsed = time.time() - start
        
        print(f"\nUser search: {elapsed:.4f}s")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "perf_user_99999")
        self.assertLess(elapsed, 0.1)
        
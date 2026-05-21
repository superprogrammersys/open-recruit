from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    ROLES = [
        ('recruiter', 'Recruiter'),
        ('manager', 'Manager'),
    ]
    role = models.CharField(max_length=20, choices=ROLES)
    
    class Meta:
        indexes = [
            models.Index(fields=['role'], name='user_role_idx'),
        ]

class Job(models.Model):
    JOB_TYPES = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Contract', 'Contract'),
        ('Internship', 'Internship'),
    ]
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_open = models.BooleanField(default=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='Full-time')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_jobs')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company}  ({self.job_type})"

    class Meta:
        indexes = [
            models.Index(fields=['is_open', 'job_type'], name='open_jobs_type_idx'),
            models.Index(fields=['company'], name='job_company_idx'),
            models.Index(fields=['-created_at'], name='job_latest_idx'),
        ]

class Application(models.Model):
    STAGES = [
        ("new", "New"),
        ("screening", "Screening"),
        ("interview", "Interview"),
        ("offer", "Offer"),
        ("rejected", "Rejected"),
        ("hired", "Hired"),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    candidate_full_name = models.CharField(max_length=50)
    stage = models.CharField(max_length=20, choices=STAGES, default="new")
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['job',
            'candidate_full_name'], name='unique_application_for_job'),
        ]
        indexes = [
            models.Index(fields=['job', 'stage'], name='app_job_stage_idx'),
            models.Index(fields=['candidate_full_name'], name='app_candidate_idx'),
            models.Index(fields=['added_by'], name='app_recruiter_idx'),
            models.Index(fields=['-created_at'], name='app_latest_idx'),
        ]
    
    def __str__(self):
        return f"{self.candidate_full_name} - {self.job.title}"
        
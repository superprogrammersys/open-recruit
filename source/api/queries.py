from .models import User, Job, Application


def get_all_users():
    return User.objects.all()

def get_users_by_role(role):
    return User.objects.filter(role=role)

def get_open_jobs():
    return Job.objects.filter(is_open=True)

def get_closed_jobs():
    return Job.objects.filter(is_open=False)

def get_applications_for_job(job_id):
    return Application.objects.filter(job_id=job_id)

def get_applications_by_stage(stage):
    return Application.objects.filter(stage=stage)

def get_all_applications():
    return Application.objects.all()

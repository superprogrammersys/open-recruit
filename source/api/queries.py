from .models import User, Job, Application


def get_all_users():
    return User.objects.all()

def get_users_by_role(role):
    return User.objects.filter(role=role)

def get_open_jobs():
    return Job.objects.filter(is_open=True).select_related('created_by')

def get_closed_jobs():
    return Job.objects.filter(is_open=False).select_related('created_by')

def get_applications_for_job(job_id):
    return Application.objects.filter(job_id=job_id).select_related('added_by', 'job')

def get_applications_by_stage(stage):
    return Application.objects.filter(stage=stage).select_related('added_by', 'job')

def get_all_applications():
    return Application.objects.all().select_related('added_by', 'job')

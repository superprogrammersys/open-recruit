from rest_framework import serializers
from api.models import (
    User,
    Job,
    Application,
    )

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('this email is already in use')
        return value

    def validate_role(self, value):
        valid_roles = ['recruiter', 'manager']
        if value not in valid_roles:
            raise serializers.ValidationError('only manager and recruiter is allowed')
        return value


    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',          # للكتابة فقط (سنضبطه لاحقاً)
            'first_name',
            'last_name',
            'role',
            'is_active',
            'is_superuser',
            'is_staff',
            'last_login',
            'date_joined',
        ]

        read_only_fields = [
            'id',
            'last_login',
            'date_joined',
            'is_superuser',
            'is_staff',
        ]

class JobSerializer(serializers.ModelSerializer):
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError('job title cannot be empty')
        return value.strip()

    def validate_company(self, value):
        if not value.strip():
            raise serializers.ValidationError('company name cannot be empty')
        return value.strip()

    def validate_job_type(self, value):
        valid_types = ['Full-time', 'Part-time', 'Contract', 'Internship']
        if value not in valid_types:
            raise serializers.ValidationError(f'job type should be one of the following types: {", ".join(valid_types)}')
        return value
    class Meta:
        model = Job
        fields = [
        'id',
        'title',
        'company',
        'description',
        'is_open',
        'job_type',
        'created_by',
        'created_at',
    ]
        read_only_fields = [
            'id',
            'created_by',
            'created_at',
        ]

class ApplicationSerializer(serializers.ModelSerializer):
    def validate_candidate_full_name(self, value):
        if not value.strip():
            raise serializers.ValidationError('candidate full name cannot be empty')
        if len(value.strip()) < 3:
            raise serializers.ValidationError('candidate full name should be at least 3 characters')
        return value.strip()

    def validate_stage(self, value):
        valid_stages = ['new', 'screening', 'interview', 'offer', 'rejected', 'hired']
        if value not in valid_stages:
            raise serializers.ValidationError(f'the stage should be one of the following: {", ".join(valid_stages)}')
        return value

    def validate(self, data):
        if self.instance:
            return data
    
        job = data.get('job')
        candidate_name = data.get('candidate_full_name')
        
        if Application.objects.filter(job=job, candidate_full_name__iexact=candidate_name).exists():
            raise serializers.ValidationError({
                                'candidate_full_name': 'this candidate has already applied to this job'
                                        })
        return data

    class Meta:
        model = Application
        fields = [
        'id',
        'job',
        'candidate_full_name',
        'stage',
        'added_by',
        'notes',
        'created_at',
        'updated_at',
        ]
        read_only_fields = [
            'id',
            'added_by',
            'created_at',
            'updated_at',
        ]

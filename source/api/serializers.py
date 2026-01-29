from rest_framework import serializers
from api.models import (
    User,
    Job,
    Application,
    )

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        read_only_fields = [
            'id',
            'last_login',
            'date_joined',
            'is_superuser',
            'is_staff',
        ]

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = [
            'id',
            'created_by',
            'created_at',
        ]

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = [
            'id',
            'added_by',
            'created_at',
            'updated_at',
        ]

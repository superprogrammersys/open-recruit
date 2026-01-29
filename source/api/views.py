from rest_framework import viewsets

from api.serializers import (
    UserSerializer,
    JobSerializer,
    ApplicationSerializer
    )
from api.queries import (
    get_all_users,
    get_open_jobs,
    get_applications_for_job,
    get_applications_by_stage,
    get_all_applications
    )
from api.paginations import StandardCursorPagination, UserCursorPagination
from api.permissions import IsManager, IsRecruiter, IsAuthenticated


# Create your views here.

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManager]
    serializer_class = UserSerializer
    pagination_class = UserCursorPagination

    def get_queryset(self):
        return get_all_users()

class JobViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManager]
    serializer_class = JobSerializer
    pagination_class = StandardCursorPagination

    def get_queryset(self):
        return get_open_jobs()

class ApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsRecruiter]
    serializer_class = ApplicationSerializer
    pagination_class = StandardCursorPagination

    def get_queryset(self):
        stage = self.request.query_params.get("stage")
        if stage:
            return get_applications_by_stage(stage)
        return get_all_applications()

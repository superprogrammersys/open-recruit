from rest_framework.routers import DefaultRouter
from api.views import UserViewSet, JobViewSet, ApplicationViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'applications', ApplicationViewSet, basename='application')

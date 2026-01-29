from rest_framework.pagination import CursorPagination


class UserCursorPagination(CursorPagination):
    page_size = 20
    ordering = '-date_joined'

class StandardCursorPagination(CursorPagination):
    page_size = 20
    ordering = '-created_at'

from rest_framework import status
from rest_framework.exceptions import APIException


class BlogException(APIException):
    status_code = status.HTTP_200_OK

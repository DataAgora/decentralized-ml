from django.urls import path
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView, RedirectView

from rest_framework.routers import DefaultRouter
from rest_framework_swagger.views import get_swagger_view
from rest_framework.documentation import include_docs_urls

from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token, verify_jwt_token

urlpatterns = [
    url(r'^docs/', include_docs_urls(title='Enterprise Auth API', description='RESTful API for Authentication.')),
    path('secret_admin_/', admin.site.urls),

    # User Authentication
    url(r'^auth/', include('rest_auth.urls')),
    url(r'^auth/registration/', include('rest_auth.registration.urls')),
    url(r'^auth/token/obtain', obtain_jwt_token),
    url(r'^auth/token/refresh', refresh_jwt_token),
    url(r'^auth/token/verify', verify_jwt_token),
]

from django.contrib import admin
from django.contrib.auth.models import User

from enterprise_users.models import EnterpriseUserProfile

admin.site.register(EnterpriseUserProfile)

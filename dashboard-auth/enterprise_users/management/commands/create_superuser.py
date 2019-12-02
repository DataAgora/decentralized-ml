import os

from django.core.management.base import BaseCommand

from django.contrib.auth.models import User
#from users.models import UserProfile

class Command(BaseCommand):

    def handle(self, *args, **options):
        username = os.environ['SUPER_USER_NAME']
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username,
                                          os.environ['SUPER_USER_EMAIL'],
                                          os.environ['SUPER_USER_PASSWORD'])

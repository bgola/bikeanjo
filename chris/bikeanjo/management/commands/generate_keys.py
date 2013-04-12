# coding: utf-8

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from bikeanjo.models import RegistrationKey

from utils import generate_secret_key

class Command(BaseCommand):
    args = ''
    help = 'Generate keys for all users'

    def handle(self, *args, **options):
        users = User.objects.all()
        
        n = 0
        for user in users:
            try:
                RegistrationKey.objects.get(user__email=user.email)
            except RegistrationKey.DoesNotExist:
                RegistrationKey.objects.create(key=generate_secret_key(12), user=user)
                n += 1
        
        self.stdout.write("Created %d new keys" % n)

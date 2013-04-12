# coding: utf-8

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from bikeanjo.models import Profile
from utils import generate_username

import csv, random

def create_profile(line):
    first_name = line[1].split()[0]
    last_name = line[1].split()[-1]
    email = line[3]
    if not email: return None
    username = email.split('@')[0][:30]
    username = generate_username(username)
    user = User.objects.create_user(username, email)
    user.first_name = first_name
    user.last_name = last_name
    user.set_unusable_password()
    user.save()
    user_created = True
    
    phone = "".join(c for c in line[2] if c.isdigit())[:20]
    city = line[12].split("/")[0].strip()[:100]
    
    sep = '-'
    if '/' in line[12]:
        sep = '/'

    try:   
        state = line[12].split(sep)[1].strip().upper()[:2]
    except IndexError:
        state = ""
    
    profile = Profile.objects.create(
            user=user, 
            phone=phone,
            state=state,
            city=city,
            active=True,
            is_bikeanjo=True
    )
    return profile

class Command(BaseCommand):
    args = '<csv_file>'
    help = 'Import profile data from a csv file'

    def handle(self, *args, **options):
        n=0
        if len(args) != 1:
            raise CommandError('Please specify one csv file')

        try:
            file = open(args[0], 'rt')
        except IOError:
            raise CommandError('File %s does not exist' % args[0])
            
        file.readline() # header
        for line in csv.reader(file):
            profile = create_profile(line)
            if profile:
                n+=1
        self.stdout.write('Successfully imported %d profiles\n' % n)

# coding: utf-8
import random

from django.contrib.auth.models import User

ALLOWED_KEYS="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def generate_secret_key(length):
    key = ""
    for i in range(length):
        key += random.choice(ALLOWED_KEYS)
    return key

def generate_username(string):
    username = string
    while User.objects.filter(username=username):
        username += str(random.randint(ord('A'), ord('Z')+1))
    return username


# coding: utf-8

from socialregistration import signals

from chris.bikeanjo.models import Profile

def setup_initial_user_data(sender, user, profile, client, **kwargs):
    fb_data = client.graph.get_object('me')
    try:
        our_user = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        our_user = Profile(user=user)
    our_user.user.first_name = fb_data['first_name']
    our_user.user.last_name = fb_data['last_name']
    bday = fb_data['birthday'].split("/")
    our_user.birthday = "-".join((bday[2],bday[0],bday[1]))
    our_user.user.email = fb_data['email']
    our_user.gender = fb_data['gender'][0]
    location = fb_data.get('location', None)
    if location is not None:
        our_user.city = fb_data['location']['name'].split(',')[0]
    our_user.user.save()
    our_user.save()

signals.connect.connect(setup_initial_user_data)

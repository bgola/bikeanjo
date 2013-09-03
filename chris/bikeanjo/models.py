# coding: utf-8
from __future__ import division
from django.db import models
from django.contrib.auth.models import User as User
from django.contrib.localflavor.br.forms import BRPhoneNumberField, BRStateSelect
from django.contrib.gis.db import models as gis_models
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib.gis.measure import D
from django.conf import settings
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.template import Template, Context

from collections import defaultdict
from chris.mailer import send_mail

import datetime
import simplejson

RADIUS = 3

gender_choices = (('m', _('Male')), ('f', _('Female')))
cycling_since_CHOICES = [ (e, e) for e in (_('less than one year'), _('between one and two years'), _('between two and four years'), _('more than 4 years')) ]

class Profile(models.Model):
    user = models.ForeignKey(User)
    is_bikeanjo = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    revisado = models.BooleanField(default=False)

    gender = models.CharField(max_length=2, choices=gender_choices)
    birthday = models.DateField(_("Birth date"), null=True, blank=False)
    phone = models.CharField(_("Phone number"), max_length=20, null=True, blank=True)
    state = models.CharField(_("Province/State"), max_length=30, null=True)
    city = models.CharField(_("City"), max_length=100)
    active = models.BooleanField(_("I'm currently available to accept requests"), default=True)

    cycling_since = models.CharField(_("How long have you been cycling?"), max_length=255, choices=cycling_since_CHOICES)
    commute_by_bike = models.CharField(_("Do you commute by bike?"), choices=(('y', _('Yes')), ('n', _('No'))), max_length=1)
    other_groups = models.TextField(_("Are you member of any NGO or other group? If yes please include any URLs"), blank=True)
    social_networks = models.TextField(_("Do you keep any blog, twitter or any other social profile on the web that may be relevant?"), blank=True)
    
    service_routes = models.BooleanField(_("routes"))
    service_accompaniment = models.BooleanField(_("accompaniment to ride"))
    service_teach = models.BooleanField(_("teach how to a bike"))
    service_institute = models.BooleanField(_("institutional events"))

    know_tech = models.SmallIntegerField(_("Mechanics/Fixing bikes"), choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5)), default=0, blank=True)
    know_security = models.SmallIntegerField(_("Security"), choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5)), default=0, blank=True)
    know_law = models.SmallIntegerField(_("Laws"), choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5)), default=0, blank=True)
    know_routes = models.SmallIntegerField(_("Routes"), choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5)), default=0, blank=True)

    agreement_bikeanjo = models.BooleanField(_("Bikeanjo agreement"))

    def __unicode__(self):
        return "%s <%s>" % (self.user.get_full_name(), self.user.email)

    def check_points(self):
        for point in self.point_set.all():
            if not point.label or self.point_set.filter(geometry__distance_gt=(point.geometry, D(km=70))).count() > 0:
                return False
        return True
    
    def find_wrong_points(self):
        wrong = []
        for point in self.point_set.all():
            if not point.label:
                wrong.append(point)
                continue
            if self.point_set.filter(geometry__distance_gt=(point.geometry, D(km=70))).count() > 1:
                wrong.append(point)
        return set(wrong)

    def save_points(self, json):
        self.point_set.all().delete()
        positions = simplejson.loads(json)
        for point in positions:
            self.point_set.create( 
                    label=point['label'][:200],
                    geometry="POINT(%s %s)" % (point['lng'], point['lat'])
                )

    def __init__(self, *args, **kwargs):
        super(Profile, self).__init__(*args, **kwargs)
        self.__original_approved = self.approved

    def save(self, *args, **kwargs):
        s = super(Profile, self).save(*args, **kwargs)
        if self.approved and not self.__original_approved:
            email_msg = EmailMessage.objects.get(email="bikeanjo-aprovado")
            email_subject = Template(email_msg.subject).render(Context({'bike_anjo_full_name': self.user.get_full_name()}))
            email_txt = Template(email_msg.text).render(Context({'bike_anjo_full_name': self.user.get_full_name()}))
            send_mail(email_subject, email_txt, 'acompanhamento@bikeanjo.com.br', [self.user.email])
        self.__original_approved = self.approved
        return s

class Point(models.Model):
    user = models.ForeignKey(Profile)
    label = models.CharField(max_length=200)
    geometry = gis_models.PointField(srid=4326)

    objects = gis_models.GeoManager()
   
    def lat(self):
        return str(self.geometry.y).replace(",", ".")

    def lng(self):
        return str(self.geometry.x).replace(",", ".")

    def __unicode__(self):
        return self.label

class Request(models.Model):
    user = models.ForeignKey(Profile, related_name="requests_made", null=True, blank=True)
    bikeanjo = models.ForeignKey(Profile, related_name="requests", blank=True, null=True)
    refused_by = models.TextField(default="", blank=True)
    datetime = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    service = models.CharField(_("Request type"), max_length=50, 
            choices=(('rota', _('route')),
                     ('acompanhamento', _('accompaniment to ride')),
                     ('aprender a pedalar', _('learn how to ride a bicycle'))
            )
        )
    
    status = models.CharField(max_length=11,
            choices = (('ONGOING', _('Processing')),
                       ('WAITING', _('Waiting')),
                       #('USER', _('Waiting for your input')),
                       #('SCHEDULED', _('Scheduled')),
                       ('FINISHED', _('Finished')),
                       #('CHECKED', _('Verified')),
                       ('IMPOSSIBLE', _('Impossible')),
                       ('CANCELED', _('Canceled'))
            )
        )

    departure = gis_models.PointField(srid=4326, null=True)
    departure_label = models.CharField(max_length=200)
    arrival = gis_models.PointField(srid=4326, null=True)
    arrival_label = models.CharField(max_length=200)

    last_modification = models.DateTimeField(auto_now=True, null=True, blank=True)

    info = models.TextField(_("More information about the request"))
    agreement = models.BooleanField(_("Read and Agree"))

    objects = gis_models.GeoManager() 

    def timedelta(self):
        return datetime.datetime.now() - self.datetime 
    def find_bike_anjo(self, exclude=None):
        query = Point.objects.filter(user__approved=True, user__active=True).exclude(user=self.user)
        if exclude:
            query = query.exclude(user__pk__in=exclude)

        if self.service == u'rota':
            query = query.filter(user__service_routes=True)
        elif self.service == u'acompanhamento':
            query = query.filter(user__service_accompaniment=True)

        bikeanjos_departure = query.filter(geometry__distance_lt=(self.departure, D(km=RADIUS)))
        bikeanjos_departure = bikeanjos_departure.distance(self.departure)
        bikeanjos_departure = bikeanjos_departure.order_by('distance')[:50]

        bikeanjos_arrival = query.filter(geometry__distance_lt=(self.arrival, D(km=RADIUS))
                        ).distance(self.arrival
                            ).order_by('distance')[:50]

        points = list(bikeanjos_arrival) + list(bikeanjos_departure)

        anjos = defaultdict(lambda: {'count': 0, 'distance': 0.0})
        for point in points:
            anjos[point.user]['count'] += 1
            anjos[point.user]['distance'] += point.distance.m

        if anjos:
            anjo = sorted(anjos, key=lambda x: anjos[x]['distance']/anjos[x]['count'])[0]
            return anjo
        return None
    
    def do_matching(self):
        exclude = [int(r) for r in self.refused_by.split(';') if r.isdigit()]
        if self.bikeanjo:
            # if it was already linked to other bikeanjo it means that the
            # bikeanjo refused the request
            exclude.append(self.bikeanjo.pk)
            self.refused_by = ';'.join(map(str, exclude))

        self.bikeanjo = self.find_bike_anjo(exclude)

        if not self.bikeanjo:
            # if we cant find a bikeanjo or tried more than 5 times, mark as impossible
            self.mark_as_impossible()
        elif self.bikeanjo.requests.exclude(status__in=('FINISHED', 'CHECKED', 'IMPOSSIBLE')).count() >= 3:
            # if we have more than 3 open requests for this Bike Anjo, we should try again the matching 
            # excluding this Bike Anjo
            return self.do_matching()
        else:
            self.mark_as_ongoing()
        self.save()

    def cancel(self):
        self.status = "CANCELED"
        self.save()

    def mark_as_impossible(self):
        self.status = 'IMPOSSIBLE'
        self.send_mail()
        self.send_mail_staff(EmailMessage.objects.get(email='impossible-staff'))
        self.save()

    def mark_as_waiting(self):
        self.status = 'WAITING'
        self.send_mail()
        self.save()

    def mark_as_ongoing(self):
        self.status = 'ONGOING'
        self.send_mail()
        self.save()

    def mark_as_finished(self):
        self.status = 'FINISHED'
        self.save()

    def send_mail_staff(self, email_msg=None, subject=None, email=None):
        if email_msg:
            subject = Template(email_msg.subject).render(Context({'full_name': self.user.user.get_full_name()}))

            email = Template(email_msg.text).render(Context({'request': self,
                                            'full_name': self.user.user.get_full_name(),
                                            'service': self.get_service_display()}))

        return send_mail(subject, email, 'sistema@bikeanjo.com.br', ['diversos@bikeanjo.com.br', 'brunogola@gmail.com'])


    def send_mail(self, subject=None, email_msg=None):
        if self.bikeanjo:
            baemail = self.bikeanjo.user.email
            baname = self.bikeanjo.user.get_full_name()
        else:
            baemail = None
            baname = None

        if email_msg is None:
            try:
                email_msg = EmailMessage.objects.get(email=self.status.lower())
            except EmailMessage.DoesNotExist:
                email = render_to_string('emails/requests/%s.txt' % self.status.lower(), {'request': self})
        
        if email_msg is not None:
            subject = Template(email_msg.subject).render(Context({'full_name': self.user.user.get_full_name(),
                                                                  'bike_anjo_full_name': baname}))

            email = Template(email_msg.text).render(Context({'request': self, 
                                            'full_name': self.user.user.get_full_name(),
                                            'service': self.get_service_display(),
                                            'bike_anjo_full_name': baname}))

        uemail = self.user.user.email
        recipients = {  'ONGOING': [baemail], 
                        'WAITING': [baemail, uemail],
                        'IMPOSSIBLE': [uemail]}
        return send_mail(subject, email, 'sistema@bikeanjo.com.br', recipients[self.status])

    def __unicode__(self):
        return "(%s) %s" % (self.datetime.strftime("%Y/%m/%d %H:%M"), self.get_status_display())


class RegistrationKey(models.Model):
    key = models.CharField(max_length=12)
    user = models.ForeignKey(Profile)
    activated = models.BooleanField()
    sent = models.BooleanField()

    def email(self):
        return self.user.user.email

    def __unicode__(self):
        site = Site.objects.get(pk=settings.SITE_ID)
        return 'http://' + site.domain + self.get_absolute_url()

    def activate(self):
        self.activated = True
        self.save()

    def get_absolute_url(self):
        return reverse("activate",args=(self.key,))


class EmailMessage(models.Model):
    email = models.CharField(max_length=50)
    subject = models.CharField(max_length=255)
    text = models.TextField()

    def __unicode__(self):
        return self.email

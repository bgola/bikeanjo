# coding: utf-8

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template import Template, Context
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.models import User
from django.http import Http404
from django.db.models import Q

from django import forms

from bikeanjo.models import Point, Request, Profile, RegistrationKey, EmailMessage
from bikeanjo.forms import ProfileForm, RequestForm, BikeAnjoProfileForm,\
                            LoginForm, FeedbackForm, RegisterForm, RequestUpdateForm

from django.conf import settings

from mailer import send_mail

import os

feedback_msg = u"""Usuário: {0} <{1}>
Mensagem:
    {2}"""

@login_required
def feedback(request):
    form  = FeedbackForm()
    user = request.user
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            send_mail(u'Feedback: %s' % form.cleaned_data['feedback_type'], feedback_msg.format(user.get_full_name(), user.email, form.cleaned_data['feedback']), 'sistema@bikeanjo.com.br', ['acompanhamento@bikeanjo.com.br'])
            messages.add_message(request, messages.SUCCESS, _(u'Thanks for your feedback!'))
            form  = FeedbackForm()
    return render_to_response('feedback.html', {'form': form}, context_instance=RequestContext(request))
            

def home(request):
    number_of_cities = len(set(d['city'].lower().split('-')[0].strip() for d in Profile.objects.filter(is_bikeanjo=True, approved=True).values('city')))

    number_of_bikeanjos = Profile.objects.filter(is_bikeanjo=True, approved=True).count()

    if request.user.is_authenticated():
        profile = request.user.get_profile()
        ongoing_requests = profile.requests.filter(status="ONGOING")
        waiting_requests = profile.requests.filter(status="WAITING")
        number_of_requests = profile.requests.exclude(status='ONGOING').count()
        return render_to_response('home-auth.html', 
                {'ongoing_requests': ongoing_requests,
                 'waiting_requests': waiting_requests,
                 'total_open_requests': ongoing_requests.count() + waiting_requests.count(),
                 'number_of_requests': number_of_requests,
                 'number_of_cities': number_of_cities,
                 'number_of_bikeanjos': number_of_bikeanjos}, context_instance=RequestContext(request))

    if request.GET.get('next', False) is not False:
        request.session['next'] = request.GET.get('next')
    login_form = LoginForm()
    return render_to_response('home.html', 
            {'login_form': login_form,
             'number_of_cities': number_of_cities,
             'number_of_bikeanjos': number_of_bikeanjos}, context_instance=RequestContext(request))

def activate(request, key):
    try:
        key = RegistrationKey.objects.get(key=key, activated=False)
    except RegistrationKey.DoesNotExist:
        return HttpResponseRedirect(reverse('home'))

    # trick to login the user without auth
    key.user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, key.user)
    key.activated = True
    key.save()
    return HttpResponseRedirect(reverse('profile'))

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            try:
                user_by_email = User.objects.get(email__iexact=form.cleaned_data['email'])
            except User.DoesNotExist:
                messages.add_message(request, messages.ERROR, _('Could not authenticate: please verify your e-mail/password'))
                return HttpResponseRedirect(reverse('home'))
            user = authenticate(username=user_by_email.username, password=form.cleaned_data['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                else:
                    messages.add_message(request, messages.ERROR, _('Could not authenticate: your account has been disabled'))
            else:
                messages.add_message(request, messages.ERROR, _('Could not authenticate, please verify your e-mail/password'))
    return HttpResponseRedirect(request.session.get('next', reverse('home')))

@login_required
def logout(request):
    auth_logout(request)
    return HttpResponseRedirect(reverse('home'))

    
@login_required
def profile(request):
    profile = request.user.get_profile()
    if profile.is_bikeanjo or request.session.get('bikeanjo', False):
        FormClass = BikeAnjoProfileForm
        points = profile.point_set.all()
    else:
        points = []
        FormClass = ProfileForm
    form = FormClass(instance=profile)
    form.initial['name'] = request.user.get_full_name()
    if profile.birthday:
        form.initial['birthday'] = profile.birthday.strftime("%d/%m/%Y")
    if request.method == 'POST':
        ok = True
        form = FormClass(request.POST, instance=profile)
        if not request.user.has_usable_password():
            form.fields['password1'].required = True
            form.fields['password2'].required = True
        if form.is_valid():
            profile = form.save()
            profile.save()
        else: 
            ok = False
            messages.add_message(request, messages.ERROR, _('Please check the errors in the form below'))
            # so we can have the points even if the form is not valid 
            profile.save_points(form.data['points_json'])
       
        if not profile.check_points():
            ok = False
            if points.count() <= 2:
                ps = points
                points = list(ps)
                ps.delete()
                messages.add_message(request, messages.ERROR, _('Please check again your points in the map'))
            else:
                wrong_points = profile.find_wrong_points()
                for point in wrong_points:
                    if point.label:
                        messages.add_message(request, messages.ERROR, 
                            _('Error saving the point %s, please add the point again and check the location') % point.label)
                    else:
                        messages.add_message(request, messages.ERROR,
                            _('You must set a label for all points'))
                    point.delete()
        if ok:
            messages.add_message(request, messages.SUCCESS, _('Profile successfully updated :-)'))
    return render_to_response('profile.html', 
               {'points': points,
                'form': form,
                'cities': set(d['city'].title().split('-')[0].strip() for d in Profile.objects.filter(is_bikeanjo=True, approved=True).values('city'))}, 
            context_instance=RequestContext(request))

def register(request, bikeanjo):
    # generic register view
    if request.user.is_authenticated():
        messages.add_message(request, messages.SUCCESS, _(u"You are already logged in!"))
        return HttpResponseRedirect(reverse('home'))
    
    show_popup = request.session.get('show_popup', True)
    request.session['show_popup'] = False
    if bikeanjo:
        request.session['quero-ser-um-bikeanjo'] = True
        redirect = reverse("profile")+"#aboutme"
        template = "register_bikeanjo.html"
        email_msg = EmailMessage.objects.get(email="novo-bikeanjo")
    else:
        request.session['solicite-um-bikeanjo'] = True
        redirect = reverse("requests")
        template = "register_normal_user.html"
        email_msg = None

    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        form.fields['password1'].required = True
        form.fields['password2'].required = True
        if form.is_valid():
            profile = form.save()
            profile.is_bikeanjo = bikeanjo
            profile.approved = False
            profile.save()
            user = authenticate(username=profile.user.username, password=form.cleaned_data['password1'])
            login(request, user)
            if email_msg is not None:
                email_subject = Template(email_msg.subject).render(Context({'bike_anjo_full_name': profile.user.get_full_name()}))
                email_txt = Template(email_msg.text).render(Context({'bike_anjo_full_name': profile.user.get_full_name()}))
                send_mail(email_subject, email_txt, 'acompanhamento@bikeanjo.com.br', [profile.user.email])
            return HttpResponseRedirect(redirect)
    return render_to_response(template, 
            {'form': form,
             'show_popup': show_popup,
             'cities': set(d['city'].title().split('-')[0].strip() for d in Profile.objects.filter(is_bikeanjo=True, approved=True).values('city'))}, 
            context_instance=RequestContext(request))

def register_bikeanjo(request):
    return register(request, True)

def register_normal_user(request):
    return register(request, False)

@login_required
def requests(request):
    profile = request.user.get_profile()
    requests_made = profile.requests_made.all()
    requests = profile.requests.all()
    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            req = form.save()
            req.user = profile
            req.status = "ONGOING"
            req.do_matching()
            req.save()
            form = RequestForm()
            messages.add_message(request, messages.SUCCESS, _(u"Seu pedido foi enviado e em breve um Bike Anjo entrará em contato 0=D"))
    else:
        form = RequestForm()
    return render_to_response('requests.html', 
               {'form': form, 
                'requests': requests,
                'requests_made': requests_made}, 
            context_instance=RequestContext(request))

@login_required
def request_accept(request, id):
    try:
        req = Request.objects.get(pk=id, status='ONGOING', bikeanjo=request.user.get_profile())
    except Request.DoesNotExist:
        messages.add_message(request, messages.ERROR, _(u"O pedido já foi atendido ou não existe"))
    else:
        req.mark_as_waiting()
        messages.add_message(request, messages.SUCCESS, _(u"Obrigado por aceitar o pedido de Bike Anjo. Em breve você estará em contato com @ iniciante! 0=D"))
    return HttpResponseRedirect(reverse('home'))

@login_required
def request_finish(request, id):
    try:
        req = Request.objects.get(pk=id, bikeanjo=request.user.get_profile())
    except Request.DoesNotExist:
        raise Http404

    req.mark_as_finished()
    messages.add_message(request, messages.SUCCESS, _(u"Obrigado, pedido marcado como finalizado com sucesso 0=D"))
    return HttpResponseRedirect(reverse('home'))

@login_required
def request_refuse(request, id):
    try:
        req = Request.objects.get(pk=id, bikeanjo=request.user.get_profile())
    except Request.DoesNotExist:
        messages.add_message(request, messages.ERROR, _(u"O pedido já foi atendido ou não existe"))
    else:
        req.do_matching()
        messages.add_message(request, messages.SUCCESS, _(u"O pedido foi cancelado e estamos encaminhando para outro Bike Anjo. Obrigado! 0=D"))
    return HttpResponseRedirect(reverse('home'))

@login_required
def request_cancel(request, id):
    try:
        req = Request.objects.get(pk=id, bikeanjo=request.user.get_profile())
    except Request.DoesNotExist:
        raise Http404

    messages.add_message(request, messages.SUCCESS, _(u"O pedido foi cancelado. Obrigado! 0=D"))
    req.cancel()
    return HttpResponseRedirect(reverse('home'))


def marker(request, big=False):
    img = "img/bike-anjo-marker.png"
    if big: 
        img = "img/bike-anjo-marker-bigmap.png"
    return HttpResponseRedirect(os.path.join(settings.STATIC_URL, img))

@login_required
def map(request):
    if request.user.is_staff:
        points = Point.objects.all()
        return render_to_response('map.html', 
                {'points': points}, context_instance=RequestContext(request))
    return HttpResponseRedirect(reverse('home'))


from socialregistration.contrib.facebook.views import FacebookSetup
class SocialSetup(FacebookSetup):
    def get(self, request):
        client = request.session[self.get_client().get_session_key()]
                
        # Get the lookup dictionary to find the user's profile
        lookup_kwargs = self.get_lookup_kwargs(request, client)

        if request.user.is_authenticated():
            profile, created = self.get_or_create_profile(request.user,
                save=True, **lookup_kwargs)

            # Profile existed - but got reconnected. Send the signal and 
            # send the 'em where they were about to go in the first place.
            self.send_connect_signal(request, request.user, profile, client)
            return self.redirect(request)

        # Logged out user - let's see if we've got the identity saved already.
        # If so - just log the user in. If not, create profile and redirect
        # to the setup view 
        user = self.authenticate(**lookup_kwargs)
        bikeanjo = False
        if user is None:
            email = client.graph.get_object('me').get('email', 'no-email-available')
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # user does not exist in our database, so we see if it's a new bikeanjo
                # and allow the creation of a new user
                if request.session.get('quero-ser-um-bikeanjo', False):
                    bikeanjo = True
                    user = self.create_user()
                elif request.session.get('solicite-um-bikeanjo', False):
                    user = self.create_user()
                else:
                    # if it's not a new bikeanjo, we deny the auth
                    messages.add_message(request, messages.ERROR, _("Sorry, invalid Facebook account"))
                    return HttpResponseRedirect(reverse('home'))

            profile = self.create_profile(user, **lookup_kwargs)
            profile.is_bikeanjo = bikeanjo
            self.store_user(request, user)
            self.store_profile(request, profile)
            self.store_client(request, client)
            return HttpResponseRedirect(reverse('socialregistration:setup'))

        # Active user with existing profile: login, send signal and redirect
        self.login(request, user)
        profile = self.get_profile(user=user, **lookup_kwargs)
        self.send_login_signal(request, user, profile, client)
        
        return self.redirect(request)

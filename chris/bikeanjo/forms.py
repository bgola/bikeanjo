# coding: utf-8
from django import forms
from django.forms.fields import ChoiceField, CharField, BooleanField
from django.forms.widgets import RadioSelect, HiddenInput
from django.contrib.localflavor.br.forms import BRPhoneNumberField, BRStateSelect
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib import auth
from django.contrib.auth.models import User


from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, ButtonHolder, Fieldset, Submit, HTML, Field, MultiField

from models import Profile, Request, gender_choices
from chris.utils import generate_username

import simplejson

google_map = u"""<div id='mymap' style='position: absolute; margin-top: -70px;'></div><h3>{0}</h3><p class="help">{1}</p>
<a class="manual_imgs" href='#'>""" + _("How to use the map?") + """</a></p>
<div id="map">
<input type="text" id="address" class='textinput textInput addressField' style="width: 99%;" /><div class="map_canvas_wrapper"><div id="map_canvas"></div></div>
</div>
<div id="map_locations">
<input style="float: left; margin-right: 5px;" type="button" onclick="bmap.codeAddress('#address')" value="Buscar" id="search-location"/>
<input type="button" onclick="saveMarker()" value="Adicionar" id="add-location"/>
<ul id="locations">
</ul>
</div><div style="clear: both;"></div>
"""

google_map_request = u"""<h3>{0}</h3><p class="help">{1}</p>
<div id="map">
<p>Endereço de saída:</p>
<input type="text" id="id_departure_label" style="width: 90%;" name='departure_label' class='textinput textInput addressField';"  /><input style="margin-left: 5px;" type="button" onclick="bmap.codeAddress('#id_departure_label')" value="Buscar" id="search-location"/>
<br />
<br />
<p>Endereço de chegada:</p>
<input type="text" id="id_arrival_label" style="width: 90%;" name='arrival_label' class='textinput textInput addressField';"  /><input style="margin-left: 5px;" type="button" onclick="bmap.codeAddress('#id_arrival_label')" value="Buscar" id="search-location"/>
<br />
<div class="map_canvas_wrapper"><div id="map_canvas"></div></div>
</div><div style="clear: both;"></div>
"""

class FeedbackForm(forms.Form):
    feedback_type = ChoiceField(choices=[ (c,c) for c in (u'Bug', u'Sugestão', u'Elogio') ], label=u"Tipo de feedback")
    feedback = CharField(label=u"Comentário",widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = "feedback-form"
        self.helper.form_method = "post"
        self.helper.form_action = "feedback"
        self.helper.form_class = "form-horizontal"
        
        self.helper.layout = Layout(
                Field('feedback_type'),
                Field('feedback'),
                ButtonHolder(
                    Submit('submit', _('Send'), css_class='btn-large')
                )
        )
        super(FeedbackForm, self).__init__(*args, **kwargs)


class LoginForm(forms.Form):
    email = forms.EmailField(label=_("E-mail"), required=True)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput())
    
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = "login-form"
        self.helper.form_method = "post"
        self.helper.form_action = "login"
        
        self.helper.layout = Layout(
                Field('email'),
                Field('password'),
                HTML('<a href="%s">%s</a>' % (reverse('password_reset'), _("Forgot your password?"))),
                ButtonHolder(
                    Submit('submit', _('Send'), css_class='btn', onclick="getAllMarkers()")
                )

        )
        super(LoginForm, self).__init__(*args, **kwargs)

class PasswordResetForm(auth.forms.PasswordResetForm):
    def clean_email(self):
        """
        Validates that an active user exists with the given email address.
        """
        email = self.cleaned_data["email"]
        self.users_cache = User.objects.filter(email__iexact=email,
                                               is_active=True)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        return email


class RequestUpdateForm(forms.ModelForm):

    class Meta:
        model = Request
        fields = ('status',)


class RequestForm(forms.ModelForm):
    agreement = BooleanField(label=_("Read and Agree"), required=True)
    points_json = CharField(widget=HiddenInput)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = "profile-form"
        self.helper.form_method = "post"
        self.helper.form_action = "requests"
        self.helper.form_class = "form-horizontal"

        self.helper.layout = Layout(
            Field('service'),
            HTML(google_map_request.format(_("Please mark the departure and the arrival destinations:"), _("Type in the boxes an address and use the map to make sure it is the right location"))),
            Fieldset(u"Mais informações",
                Field("info"),
            ),
            Field("agreement"),
            ButtonHolder(
                Submit('submit', _('Send'), css_class='btn-large', onclick="getAllMarkers()")
            )
        )
        super(RequestForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        self.cleaned_data = super(RequestForm, self).clean(*args, **kwargs)
        positions = simplejson.loads(self.cleaned_data['points_json'])
        if len(positions) < 2:
            raise forms.ValidationError(_(u"Os campos de saída e de chegada não foram preenchidos corretamente"))
        return self.cleaned_data

    def save(self, *args, **kwargs):
        request = super(RequestForm, self).save(*args, **kwargs)
        positions = simplejson.loads(self.cleaned_data['points_json'])
        request.departure = "POINT(%s %s)" % (positions[0]['lng'], positions[0]['lat'])
        request.arrival = "POINT(%s %s)" % (positions[1]['lng'], positions[1]['lat'])
        request.save()
        return request

    class Meta:
        model = Request
        exclude = ( 'departure',
                    'arrival',
                    'bikeanjo',
                    'status', 
                    'user',
                    'refused_by')

class ProfileForm(forms.ModelForm):
    name = forms.CharField(label=_("Full name"))
    phone = forms.CharField(_("Phone number"))
    gender = ChoiceField(widget=RadioSelect, choices=gender_choices)
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput(), required=False)
    password2 = forms.CharField(label=_("Repeat Password"), widget=forms.PasswordInput(), required=False)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = "profile-form"
        self.helper.form_method = "post"
        self.helper.form_action = "profile"
        self.helper.form_class = "form-horizontal"

        self.helper.layout = Layout(
             ButtonHolder(
                Submit('submit', 'Salvar', css_class='btn-large', onclick="getAllMarkers()")
            ),
            Field('name'),
            Field('birthday', css_class="dateinput textInput"),
            Field('gender'),
            Field('phone'),
            Field('city'),
            Field('state'),
            Fieldset(_("If you want to change your password:"),
                'password1',
                'password2',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-large', onclick="getAllMarkers()")
            )
        )
        super(ProfileForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        kwargs['commit'] = False
        profile = super(ProfileForm, self).save(*args, **kwargs)
        if user:
            profile.user = user
        profile.save()
        first_name = self.cleaned_data['name'].split()[0]
        last_name = " ".join(self.cleaned_data['name'].split()[1:])
        profile.user.first_name = first_name
        profile.user.last_name = last_name
        if self.cleaned_data['password1'] and self.cleaned_data['password1'] == self.cleaned_data['password2']:
            profile.user.set_password(self.cleaned_data['password1'])
        profile.user.save()
        return profile

    def clean(self, *args, **kwargs):
        self.cleaned_data = super(ProfileForm, self).clean(*args, **kwargs)
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("Passwords didn't match"))
        return self.cleaned_data

    class Meta:
        model = Profile
        exclude = ( 'user',
                    'is_bikeanjo',
                    'service_routes',
                    'service_accompaniment',
                    'service_teach',
                    'service_institute',
                    'know_tech',
                    'know_security',
                    'know_law',
                    'know_routes',
                    'agreement_bikeanjo',
                    'cycling_since',
                    'commute_by_bike',
                    'other_groups',
                    'social_networks',
                    'active',
                    'approved'
            )
        widgets = {'state': BRStateSelect() }


class RegisterForm(ProfileForm):
    register_email = CharField(label=_('E-mail'))

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "register-form"
        self.helper.form_method = "post"
        self.helper.form_style = "inline"
        self.helper.form_class = "form-horizontal"

        self.helper.layout = Layout(
            Field('name'),
            Field('register_email'),
            Field('gender'),
            Field('birthday', css_class="dateinput textInput"),
            Field('phone'),
            Field('city'),
            Field('state'),
            Field('password1'),
            Field('password2'),
            ButtonHolder(
                Submit('submit', _('Next'), css_class='btn-large')
            )
        )

    def clean(self, *args, **kwargs):
        self.cleaned_data = super(RegisterForm, self).clean(*args, **kwargs)
        if 'register_email' in self.cleaned_data:
            try:
                User.objects.get(email=self.cleaned_data['register_email'])
            except User.DoesNotExist:
                return self.cleaned_data
        raise forms.ValidationError(_("This e-mail address is already taken"))

    def save(self, *args, **kwargs):
        first_name = self.cleaned_data['name'].split()[0]
        last_name = " ".join(self.cleaned_data['name'].split()[1:])
        email = self.cleaned_data['register_email']
        username = generate_username(email.split('@')[0][:30])
        password = self.cleaned_data['password1']
        user = User.objects.create_user(username, email, password) 
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        kwargs['user'] = user
        profile = super(RegisterForm, self).save(*args, **kwargs)
        return profile

    class Meta:
        model = Profile
        exclude = ( 'user',
                    'is_bikeanjo',
                    'service_routes',
                    'service_accompaniment',
                    'service_teach',
                    'service_institute',
                    'know_tech',
                    'know_security',
                    'know_law',
                    'know_routes',
                    'agreement_bikeanjo',
                    'cycling_since',
                    'commute_by_bike',
                    'other_groups',
                    'social_networks',
                    'active',
                    'approved'
                    )
        widgets = {'state': BRStateSelect() }


class BikeAnjoProfileForm(ProfileForm):
    agreement_bikeanjo = BooleanField(label=_("Yes, I am interested on being a Bike Anjo volunteer.<br/>I won't charge for this and as a reward I only expect to see one more cyclist in the streets! :)"), required=True)
    points_json = CharField(widget=HiddenInput)
    
    def __init__(self, *args, **kwargs):
        super(BikeAnjoProfileForm, self).__init__(*args, **kwargs)

        # overrides the helper.layout to add the google map
        self.helper.layout = Layout(
            ButtonHolder(
                Submit('submit', 'Salvar', css_class='btn-large', onclick="getAllMarkers()")
            ),
            Field('active'),
            Fieldset(_('Personal data'),
                Field('name'),
                Field('birthday', css_class="dateinput textInput"),
                Field('gender'),
                Field('phone'),
                Field('city'),
                Field('state'),
            ),
            HTML("<div id='aboutme' style='position: absolute; margin-top: -70px;'></div>"),
            Fieldset(_('About you'),
                Field('cycling_since'),
                Field('commute_by_bike'),
                Field('other_groups'),
                Field('social_networks'),
            ),
            HTML(google_map.format(_("Please mark the points where you can help:"),
                _("You can select as many points as you want. Our system recognizes a range of 2mi from your selections. We recommend you to distribute on a range area that you know and are habituated to cycle from town. As more detailed, easier to find matched-requests."))),
            Fieldset(_('Mark the services you can offer:'),
                'service_routes',
                'service_accompaniment',
                'service_teach',
                'service_institute',
            ),
            Fieldset(_('From 0 to 5 tell us your knowledge about:'),
                Field('know_tech'),
                Field('know_security'),
                Field('know_law'),
                Field('know_routes'), 
                css_class="conhecimento"
            ),
            Fieldset(_("If you want to change your password:"),
                'password1',
                'password2',
            ),
            Fieldset(_("Agreement"),
                "agreement_bikeanjo",
            ),
            ButtonHolder(
                Submit('submit', 'Salvar', css_class='btn-large', onclick="getAllMarkers()")
            )
        )

    def save(self, *args, **kwargs):
        profile = super(BikeAnjoProfileForm, self).save(*args, **kwargs)
        profile.save_points(self.cleaned_data['points_json'])
        return profile

    class Meta:
        model = Profile
        exclude = ( 'user',
                    'is_bikeanjo',
                    'approved')
        widgets = {'state': BRStateSelect() }


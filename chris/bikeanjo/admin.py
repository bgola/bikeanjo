# coding: utf-8

from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core import serializers
from django.contrib.auth.models import User
from django.conf.urls.defaults import patterns

from models import Profile, Point, Request, RegistrationKey, EmailMessage
import tasks

def approve_profile(modeladmin, request, queryset):
    queryset.update(approved=True)
approve_profile.short_description = _("Mark selected profiles as approved")

def check_request(modeladmin, request, queryset):
    queryset.update(status='CHECKED')
approve_profile.short_description = _("Check request")

def find_bike_anjo(modeladmin, request, queryset):
    for req in queryset:
        req.do_matching()
find_bike_anjo.short_description = _("Find matching")

def export_emails(modeladmin, request, queryset):
    try:
        emails = ', '.join(p.user.email for p in queryset)
    except AttributeError:
        emails = ', '.join(p.user.user.email for p in queryset)
    response = HttpResponse(mimetype="text")
    response.write(emails)
    return response
export_emails.short_description = _("Export e-mails")


class RegistrationKeyInput(forms.TextInput):
    def render(self, *args, **kwargs):
        html = super(RegistrationKeyInput, self).render(*args, **kwargs)
        html += """ <a id='keygen' href="javascript:void(0)">gerar nova chave</a>
                <script>
                django.jQuery('a#keygen').click(function() {
                    var chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZ";
                    var key = '';
                    for (var i=0; i<12; i++) {
                      var rnum = Math.floor(Math.random() * chars.length);
                      key += chars.substring(rnum,rnum+1);
                    }
                    django.jQuery('input#id_registrationkey_set-0-key').val(key);
                });
                </script>"""
        
        return mark_safe(html)

class RegistrationKeyAdminForm(forms.ModelForm):
    key = forms.CharField(label=_('Key'), widget=RegistrationKeyInput())
    
    class Meta:
        model = RegistrationKey


class PointInline(admin.StackedInline):
    model = Point
    extra = 0


class RegistrationKeyInline(admin.TabularInline):
    model = RegistrationKey
    extra = 1
    max_num = 1
    
    form = RegistrationKeyAdminForm


class CompleteProfileListFilter(admin.SimpleListFilter):
    title = _('complete profile')
    parameter_name = "complete"

    def lookups(self, request, model_admin):
        return ((True, _("Yes")), (False, _("No")))

    def queryset(self, request, queryset):
        if self.value:
            return queryset.filter()
        else:
            return queryset.filter()


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_bikeanjo', 'approved', 'city', 'state', 'revisado')
    list_filter = ('state', 'approved', 'revisado', 'is_bikeanjo', 'gender','service_routes', 'service_accompaniment', 'service_teach' )
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)
    save_on_top = True

    inlines = (PointInline, RegistrationKeyInline)
    actions = (approve_profile, export_emails)

    change_form_template = 'admin/profile_change_form.html'

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        extra_context['profile_email'] = self.email(Profile.objects.get(pk=object_id))
        return super(ProfileAdmin, self).change_view(request, object_id,
            extra_context=extra_context) 

    def name(self, profile):
        return profile.user.get_full_name()

    def email(self, profile):
        return profile.user.email
    class Media:
        js = [
            'http://code.jquery.com/jquery-1.4.2.min.js', 
            'http://maps.google.com/maps/api/js?sensor=false', 
            settings.STATIC_URL +'admin/long-lat-render.js'
        ]


class HasBikeAnjoFilter(admin.SimpleListFilter):
    title = _("Has Bike Anjo")

    parameter_name = "has_bikeanjo"

    def lookups(self, request, model_admin):
        return ((True, _("Yes")), (False, _("No")))

    def queryset(self, request, queryset):
        if self.value() == "True":
            return queryset.filter(bikeanjo__isnull=False)
        elif self.value() == "False":
            return queryset.filter(bikeanjo__isnull=True)
        return queryset


class RequestCityFilter(admin.SimpleListFilter):
    title = _("City")

    parameter_name = "city"

    def lookups(self, request, model_admin):
        cities = sorted(set([ r.user.city for r in Request.objects.all() ]))
        return ((c,c) for c in cities)

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(user__city=self.value())
        return queryset


class RequestAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('datetime', 'user_30chr', 'bikeanjo_30chr', 'departure_label', 'arrival_label', 'service', 'status')
    list_filter = (HasBikeAnjoFilter, 'status', 'service', RequestCityFilter)
    ordering = ('-datetime',)

    raw_id_fields = ('user', 'bikeanjo')
    actions = (find_bike_anjo, check_request)
    
    change_form_template = 'admin/request_change_form.html'
    
    def user_30chr(self, obj):
        return "%s..." % obj.user.__unicode__()[:20]
    user_30chr.short_description = "Usuario"

    def bikeanjo_30chr(self, obj):
        return "%s..." % obj.bikeanjo.__unicode__()[:30]
    bikeanjo_30chr.short_description = "Bikeanjo"

    class Media:
        js = [
            'http://code.jquery.com/jquery-1.4.2.min.js', 
            'http://maps.google.com/maps/api/js?sensor=false', 
            settings.STATIC_URL +'admin/long-lat-render.js'
        ]
    
    def get_urls(self):
        urls = super(RequestAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^(.+)/matching/$', self.admin_site.admin_view(self.do_matching))
        )
        return my_urls + urls

    def do_matching(self, request, pk):
        req = get_object_or_404(Request, pk=pk)
        req.do_matching()
        return HttpResponseRedirect('../')

class PointAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('geometry', 'label', 'user_name', 'user_email')
    search_fields = ('label', 'user__user__email', 'user__user__first_name', 'user__user__last_name')

    def user_email(self, point):
        return point.user.user.email

    def user_name(self, point):
        return point.user.user.get_full_name()

admin.site.register(Point, PointAdmin)
admin.site.register(EmailMessage)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Request, RequestAdmin)
admin.site.register(RegistrationKey, 
        list_display=('key', 'email', 'sent', 'activated'), 
        list_filter=('sent', 'activated'), 
        search_fields=('user__user__email', 'user__first_name', 'user__last_name'),
        actions=(export_emails,)
    )

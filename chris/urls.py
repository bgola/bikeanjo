from django.conf.urls.defaults import patterns, include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.views import password_reset, password_reset_done, password_reset_confirm, password_reset_complete
from bikeanjo.forms import PasswordResetForm
from views import SocialSetup


from django.contrib import admin
admin.autodiscover()

urlpatterns = i18n_patterns('',
    url(r'^$', 'chris.views.home', name='home'),
    url(r'^profile/?$', 'chris.views.profile', name='profile'),
    url(r'^password/reset/$', password_reset, { 'template_name': 'password_reset.html',
                                                'email_template_name': 'emails/password_reset.txt',
                                                'from_email': 'sistema@bikeanjo.com.br',
                                                'password_reset_form': PasswordResetForm}, name='password_reset'),

    url(r'^password/done/$', password_reset_done, { 'template_name': 'password_reset_done.html'}, name='password_reset_done'),
    url(r'^password/confirm/(?P<uidb36>\w+)/(?P<token>[\w-]+)/$', password_reset_confirm, { 'template_name': 'password_reset_confirm.html'}, name='password_reset_confirm'),
    url(r'^password/complete/$', password_reset_complete, { 'template_name': 'password_reset_complete.html'}, name='password_reset_complete'),
    url(r'^activate/(?P<key>\w+)', 'chris.views.activate', name='activate'),
    url(r'^requests/?$', 'chris.views.requests', name='requests'),
    url(r'^requests/(?P<id>\d+)/accept/?$', 'chris.views.request_accept', name='request_accept'),
    url(r'^requests/(?P<id>\d+)/refuse/?$', 'chris.views.request_refuse', name='request_refuse'),
    url(r'^requests/(?P<id>\d+)/finish/?$', 'chris.views.request_finish', name='request_finish'),
    url(r'^requests/(?P<id>\d+)/cancel/?$', 'chris.views.request_cancel', name='request_cancel'),
    url(r'^map/', 'chris.views.map', name='map'),
    url(r'^feedback/?$', 'chris.views.feedback', name='feedback'),
    url(r'^logout/', 'chris.views.logout', name='logout'),
    url(r'^login/$', 'chris.views.login_view', name='login'),
    url(r'^quero-ser-um-bikeanjo/$', 'chris.views.register_bikeanjo', name='register_bikeanjo'),
    url(r'^solicite-um-bikeanjo/$', 'chris.views.register_normal_user', name='register_normal_user'),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('',
        url(r'^bike-anjo-marker.png$', 'chris.views.marker', name='bikeanjomarker'),
        url(r'^bike-anjo-marker-bigmap.png$', 'chris.views.marker', {'big': True}, name='bikeanjomarkerbig'),
        url(r'^social/facebook/setup/$', SocialSetup.as_view(), {}, name='social_setup'),
        url(r'^social/', include('socialregistration.urls',
                            namespace = 'socialregistration')),
        url(r'^admin_tools/', include('admin_tools.urls')),
        )

from django.conf import settings

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += i18n_patterns('',
        url(r'^translate/', include('rosetta.urls')),
    )

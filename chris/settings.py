# coding: utf-8
import os.path

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('', ''),
)

PROJECT_PATH = os.path.dirname(__file__)
HOST = 'sistema.bikeanjo.com.br'

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'bikeanjo',                      # Or path to database file if using sqlite3.
        'USER': 'user',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

TIME_ZONE = 'America/Sao_Paulo'

LANGUAGE_CODE = 'pt-br'

_ = lambda s:s
LANGUAGES = (
                ('pt-br', _('Brazilian Portuguese')),
                #('es', _('Spanish'))
                #('en', _('English'))
        )

SITE_ID = 1

USE_I18N = True
#USE_L10N = True

MEDIA_ROOT = os.path.join(PROJECT_PATH, os.pardir, "site_media/media")
STATIC_ROOT = os.path.join(PROJECT_PATH, os.pardir, "site_media/static")
MEDIA_URL = '/site_media/media/'
STATIC_URL = '/site_media/static/'
ADMIN_MEDIA_PREFIX = '/site_media/static/admin/'

STATICFILES_DIRS = (os.path.join(PROJECT_PATH, "static"),)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'NOONONNONONONONONONONONONONONONONONONON'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'pagination.middleware.PaginationMiddleware',
)

ROOT_URLCONF = 'chris.urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
)

INSTALLED_APPS = (
    # admin tools
    'admin_tools',
    'admin_tools.theming',
    'admin_tools.menu',
    'admin_tools.dashboard',
    
    # django contrib stuff
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.humanize',
    'django.contrib.gis',

    # 3rd party
    'south',
    'socialregistration',
    'socialregistration.contrib.facebook',
    'crispy_forms',
    'rosetta',
    'djcelery',
#    'postman',
#    'pagination',
#    'socialregistration.contrib.twitter'

    # custom
    'chris.mailer',

    # bikeanjo stuff
    'chris.bikeanjo',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    )

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'socialregistration.contrib.facebook.auth.FacebookAuth',
)

FACEBOOK_APP_ID = ''
FACEBOOK_SECRET_KEY = ''

FACEBOOK_REQUEST_PERMISSIONS = 'user_birthday email user_location'

SOCIALREGISTRATION_GENERATE_USERNAME = True

AUTH_PROFILE_MODULE = 'bikeanjo.Profile'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/'

ACCOUNT_ACTIVATION_DAYS = 7
DATE_INPUT_FORMATS = ("%d/%m/%Y",)

CRISPY_TEMPLATE_PACK='bootstrap'

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda o: "/profile/",
}

ADMIN_TOOLS_MENU = 'chris.menu.CustomMenu'
ADMIN_TOOLS_INDEX_DASHBOARD = 'chris.dashboard.CustomIndexDashboard'
ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'chris.dashboard.CustomAppIndexDashboard'

EMAIL_USE_TLS = True
EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

EMAIL_PORT = 587

ADMIN_TOOLS_MENU = 'chris.menu.CustomMenu'
ADMIN_TOOLS_THEMING_CSS = "admin_tools/css/admintheme.css"

try:
    from settings_local import *
except ImportError:
    pass

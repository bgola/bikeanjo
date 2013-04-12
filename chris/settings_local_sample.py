DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('You', 'you@yourdomain.com'),
)

PROJECT_PATH = os.path.dirname(__file__)
HOST = 'localhost'

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

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'yoursecrekey'

FACEBOOK_APP_ID = 'faceapp_id'
FACEBOOK_SECRET_KEY = 'face_secrect_key'

FACEBOOK_REQUEST_PERMISSIONS = 'user_birthday email user_location'

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.xxx.com'
EMAIL_HOST_USER = 'x@x.com'
EMAIL_HOST_PASSWORD = 'PASSWORD'

EMAIL_PORT = 587

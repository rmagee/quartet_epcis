# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import

import django

DEBUG = True
USE_TZ = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "+-!+mriut6%tm@v^wi4(x6pz8hga+c*^0v+yvm5#lm+&5b$8on"

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": ":memory:",
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'qu4rtettest',
        'USER': 'qu4rtet',
        'PASSWORD': 'onetwothreefour',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

ROOT_URLCONF = "tests.urls"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "quartet_epcis",
]

SITE_ID = 1

if django.VERSION >= (1, 10):
    MIDDLEWARE = ()
else:
    MIDDLEWARE_CLASSES = ()

AUTOCOMMIT = False

import logging
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[logging.StreamHandler()]
)

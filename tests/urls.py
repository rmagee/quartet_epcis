# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.conf.urls import url, include

from quartet_epcis.urls import urlpatterns as quartet_urls

urlpatterns = [
    url(r'^', include(quartet_urls, namespace='quartet_epcis')),
]

[![pipeline status](https://gitlab.com/serial-lab/quartet_epcis/badges/master/pipeline.svg)](https://gitlab.com/serial-lab/quartet_epcis/commits/master)
[![coverage report](https://gitlab.com/serial-lab/quartet/badges/master/coverage.svg)](https://gitlab.com/serial-lab/quartet/commits/master)

# QU4RTET

Quartet: The Open Source Level-4 System for the Tracking and Tracing of
serialized goods.

## Documentation


The full documentation is under the docs directory in this project.

## Quickstart


Install Quartet::

    pip install quartet

Add it to your `INSTALLED_APPS`:


    INSTALLED_APPS = (
        ...
        'quartet.apps.QuartetConfig',
        ...
    )

Add Quartet's URL patterns:

    from quartet import urls as quartet_urls


    urlpatterns = [
        ...
        url(r'^', include(quartet_urls)),
        ...
    ]

## Features

* TODO

## Running The Unit Tests

Does the code actually work?


    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox


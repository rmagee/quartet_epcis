[![pipeline status](https://gitlab.com/serial-lab/quartet_epcis/badges/master/pipeline.svg)](https://gitlab.com/serial-lab/quartet_epcis/commits/master)
[![coverage report](https://gitlab.com/serial-lab/quartet_epcis/badges/master/coverage.svg)](https://gitlab.com/serial-lab/quartet/commits/master)

# QU4RTET

Quartet: The Open Source Level-4 System for the Tracking and Tracing of
serialized goods.

## Documentation

Find the latest docs here:

[https://serial-lab.gitlab.io/quartet_epcis/](https://serial-lab.gitlab.io/quartet_epcis/)


The full (pre-built )documentation is under the docs directory in this project.

## Quickstart


Install Quartet::

    pip install quartet_epcis

Add it to your `INSTALLED_APPS`:


    INSTALLED_APPS = (
        ...
        'quartet_epcis',
        ...
    )


## Features

* Maintains the database schema for EPCIS 1.2 support.
* Parses EPCIS 1.2 XML streams to the configured backend.

## Running The Unit Tests

Does the code actually work?


    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install -r requirements_test.txt
    (myenv) $ python runtests.py


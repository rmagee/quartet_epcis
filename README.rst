QU4RTET EPCIS
=============

.. image:: https://gitlab.com/serial-lab/quartet_epcis/badges/master/pipeline.svg
        :target: https://gitlab.com/serial-lab/quartet_epcis/commits/master

.. image:: https://gitlab.com/serial-lab/quartet_epcis/badges/master/coverage.svg
        :target: https://gitlab.com/serial-lab/quartet_epcis/pipelines

.. image:: https://badge.fury.io/py/quartet_epcis.svg
    :target: https://badge.fury.io/py/quartet_epcis

Built on top of the world-class EPCPyYes python package.
Real EPCIS support for serious people running real systems.

.. code-block:: text

     ________  ___   ___  _______   ________  ________  ___  ________
    |\   __  \|\  \ |\  \|\  ___ \ |\   __  \|\   ____\|\  \|\   ____\
    \ \  \|\  \ \  \\_\  \ \   __/|\ \  \|\  \ \  \___|\ \  \ \  \___|_
     \ \  \\\  \ \______  \ \  \_|/_\ \   ____\ \  \    \ \  \ \_____  \
      \ \  \\\  \|_____|\  \ \  \_|\ \ \  \___|\ \  \____\ \  \|____|\  \
       \ \_____  \     \ \__\ \_______\ \__\    \ \_______\ \__\____\_\  \
        \|___| \__\     \|__|\|_______|\|__|     \|_______|\|__|\_________\
              \|__|                                            \|_________|

The essential Open-Source EPCIS component for the QU4RTET traceability
platform.

For more on QU4RTET see http://www.serial-lab.com

The quartet_epcis python package is a Django application that
contains the base database models necessary for the support of
EPCIS 1.2 data persistence to an RDBMS. The quartet_epcis.parsing
package contains an EPCIS XML parser that will take an input stream
of XML data and save it to a configured database back-end.

The quartet_epcis.app_models directory contains a set of
Django ORM models that are used to define the database scheme
and store EPCIS data in the database.

Documentation
-------------

Find the latest docs here:

https://serial-lab.gitlab.io/quartet_epcis/


The full (pre-built )documentation is under the docs directory in this project.

Quickstart
----------

Install QU4RTET EPCIS
---------------------

.. code-block:: text

    pip install quartet_epcis


Add it to your `INSTALLED_APPS`:

.. code-block:: text

    INSTALLED_APPS = (
        ...
        'quartet_epcis',
        ...
    )


Features
--------

* Maintains the database schema for EPCIS 1.2 support.
* Parses EPCIS 1.2 XML streams to the configured backend database system.
* Enforces business rules around decommissioning, commissioning, aggregation,
  disaggregation, etc.

Running The Unit Tests
----------------------

.. code-block:: text

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install -r requirements_test.txt
    (myenv) $ python runtests.py


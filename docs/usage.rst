=====
Usage
=====

To use quartet_epcis in a django project, add it to your `INSTALLED_APPS` in
your settings.py file:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'quartet_epcis.apps.quartet_epcis.Config',
        ...
    )

Add quartet_epcis's URL patterns:

Then run migrations:

.. code-block::

    python manage.py migrate


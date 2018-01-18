=====
Usage
=====

To use quartet_epcis in a project, add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'quartet_epcis.apps.quartet_epcisConfig',
        ...
    )

Add quartet_epcis's URL patterns:

.. code-block:: python

    from quartet_epcis import urls as quartet_epcis_urls


    urlpatterns = [
        ...
        url(r'^', include(quartet_epcis_urls)),
        ...
    ]

=====
Usage
=====

To use quartet_epcis in a django project, add it to your `INSTALLED_APPS` in
your settings.py file:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'quartet_epcis',
        ...
    )

Add quartet_epcis's URL patterns:

Then run migrations:

.. code-block:: python

    python manage.py migrate


Using the QuartetParser
=======================

The QuartetParser (see example below), provides most of the functionality
for this python package outside of the database models.  The QuartetParser
will parse an EPCIS 1.2 compliant XML document and, as EPCIS events are
parsed, will put them and their constituent data into the database.

Once you have installed the package and executed your migrations, you can
then parse any EPCIS 1.2 XML documents directly into the database as such:

.. code-block:: python

    from quartet_epcis.parsing.parser import QuartetParser

    # for example, load an xml document from the current
    # directory into the database
    curpath = os.path.dirname(__file__)

    parser = QuartetParser(
        os.path.join(curpath, 'data/epcis.xml')
    )

Using the EPCIS Database Proxy
==============================


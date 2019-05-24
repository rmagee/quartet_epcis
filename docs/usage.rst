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

The EPCIS Database Proxy class is located at
`quartet_epcis.db_api.queries.EPCISDatabaseProxy` and is documented in
the modules section of these documents.  The proxy class is in place to
abstract away the underlying database and to make querying the database
simpler from a developer's perspective.

The quartet_epcis package abstracts away the database for a few reasons. One,
if the database changes radically at some point, the clients of the
quartet_epcis APIs will never know and won't break.  Secondly, the database
layer is flattened to make the management of EPCIS data both easier from
a development perspective and for performance, tuning and flexibility reasons.

Parsing Step Settings
=====================

There is an inbound rule that accepts the following parameters:

.. list-table:: Options
    :widths: 33 33
    :header-rows: 1

    * - Name
      - Description
    * - LooseEnforcement
      - True or False- default is False, if set to true, EPCIS rules are enforced.  If set to false, the assumption is that the data is well formed and the parser will not check all business rules.
    * - Format
      - JSON or XML.  Default is XML.  If you wish to parse inbound EPCPyYES JSON formatted EPCIS, then set this to True. The step will no longer be able to parse XML once this is set so keep that in mind when planning your step configurations.

Configuring the step in a rule:

Here is the *Class Path* configuration.

.. code-block:: text

    quartet_epcis.parsing.steps.EPCISParsingStep

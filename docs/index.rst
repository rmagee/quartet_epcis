.. complexity documentation master file, created by
   sphinx-quickstart on Tue Jul  9 22:26:36 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

QU4RTET EPCIS - EPCIS XML Parsing for the Quartet Platform
=================================================================
The quartet_epcis python package is a Django application that
contains the base database models necessary for the support of
EPCIS 1.2 data persistence to an RDBMS.  The `quartet_epcis.parsing` package
contains an EPCIS XML parser that will take an input stream of XML data
and save it to a configured database back-end.

The `quartet_epcis.app_models` directory contains a set of Django ORM models
that are used to define the database scheme and store EPCIS data in the
database.

Contents
________

.. toctree::
   :maxdepth: 2


   readme
   installation
   usage
   contributing
   authors
   history
   quartet_epcis
   modules

.. :changelog:

History
-------
Each release section is appended to until a minor release is created.
Minor patches are added incrementally to the release list.

0.1.0 (2017-12-07)
++++++++++++++++++

* First release on PyPI.

1.0.+ May 4, 2018
++++++++++++++++++

* First production-ready release.
* CI build to auto-deploy tags to PyPI
* Longer fields for document and event ids.
* Changes to CI build.
* Data migration to automatically create EPCIS rule and Step.

1.0.4 June 6, 2018
++++++++++++++++++

* EPCISParsingStep in the steps module was of wrong Type...but was working
anyway.  Switched to `rule.Step` from `models.Step`.
* Added on_failure to the EPCISParsingStep to account for the new abstract
method on the base `quartet_capture.rules.Step` class.

1.1 June 21 2018
++++++++++++++++
* Addition of new business parser for EPCIS.  The business parser inherits
  from the original `quartet_epcis.parsing.parser.QuartetParser` and adds
  additional business context processing.  The new parser will perform and
  track explicit aggregation and dissagregation functions as well as maintain
  records of deleted/decommissioned events and check for events containing
  EPCs that were never commissioned.  Over 800 lines of unit testing code along
  with 30 tests now cover just the quartet_epcis parsers and API.
* Fix to aggregation handling with a more aggressive caching strategy- all
  entries are cached until the end of processing.
* Added additional ordering to models along with created and modified fields
  for the UUID based models.
* Updated LooseEnforcement check on EPCIS Parsing Step to use the boolean
  parameter helper.

1.2 August 14 2018
++++++++++++++++++
* Sorted event processing by date for both the business and standard
qu4rtet EPCIS parsers.
* Updated unit tests.

1.3 Sept 28 2018
++++++++++++++++
* Added a generic EPCIS parser that finds EPCIS elements that may or
may not contain an explicit namespace declaration.
* Changed ordering of events to be descending by event time.
* Fixed bug with get entries by event in the EPCISDBProxy class.

1.4 Jan 2 2018
++++++++++++++
* Added a new get_message_by_event_id to the EPCISDBProxy, which allows
  calling parties to retrieve an entire inbound message by providing a
  single event from that message.
* Added an additional parser that creates a cache of EPCPyYes objects
  in memory without storing to a database.  Also modified the QuartetParser
  so that it puts the Message.id on the rule context after parsing a
  full message and storing to the database.
* Added more unit tests for the new feature/functions.

1.5 June 2019
+++++++++++++
* Added a helper to the db_proxy module to return all object events
  by epc list.
* Added select_for_update parameter to the dbproxy get object events
  function.

.. :changelog:

History
-------

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

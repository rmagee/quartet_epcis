.. _proxy:
Using the EPCIS Database Proxy Class
====================================
A quick note: The quartet_epcis package defines a database schema that will look unfamiliar
to those of you with a steep history in EPCIS.  Many of the database constructs
in this schema were designed with performance and a more flattened database back-end
in mind.  For example, there is only one Event model for all four (five)
EPCIS Event types- this was done to make event look-ups efficient and is just
one example of how the database may not exactly reflect the EPCIS schema
itself.






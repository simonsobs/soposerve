HIPPO
=====

<img src="logo.svg" style="display:block;margin-left:auto;margin-right:auto;width:30%"/>

The HIerarchical Product Post Office
------------------------------------

Hippo is a piece of software aimed at making FAIR (Findable, Attributable, Interoperable,
and Reuseable) data access easier. Through the use of the very flexible MongoDB for
_true_ metadata storage and MinIO as a data storage backend, hippo provides metadata-driven
access to reusable products.

Use-Cases
---------

Hippo is under development for the Advanced Simons Observatory, an NSF-funded telescope project
that aims to study, among other things, the Cosmic Microwave Background. Throughout the project,
many pieces of data will be produced: things like images, arrays, small databases, etc. Storing
and sharing these within the collaboration, and to the public, is a huge challenge; it's easy
enough to put them all in a big folder somewhere, but without associated metadata you will never
be able to find what you're looking for.

Enter hippo! Hippo allows you to upload data products and access them both manually and
programatically through a metadata-driven interaction.
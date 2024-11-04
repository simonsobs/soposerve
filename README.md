HIPPO
=====

<p align="center">
<img src="hipposerve/web/static/logo.svg" style="width:30%"/>
</p>

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

Examples
--------

There are a number of example cases in the `example` directory. To lauch the development
server, you should run

```
python3 examples/simpleserve.py
```

This will create a test account (`admin`) with API key `TEST_API_KEY` and password
`TEST_PASSWORD`. You can use the upload scripts in `examples/{name}` that upload
data from the [NASA LAMBDA instance](https://lambda.gsfc.nasa.gov/product/act/actpol_prod_table.html).

You may need to copy `config.json` to `~/.hippo.conf` to correctly load the environment
or export appropriate variables.
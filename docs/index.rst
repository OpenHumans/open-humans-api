.. open-humans-api documentation master file, created by
   sphinx-quickstart on Tue Mar 20 13:49:57 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to open-humans-api's documentation!
*******************************************

``open-humans-api`` is a Python package that wraps the API methods of
`Open Humans <https://www.openhumans.org/>`_ for easier use in your own
Python applications and websites.

It also installs a
set of command line utilities that can be used to

* download public files

  * for a given Project
  * for a given Member

* Upload files for a project through a ``master_access_token`` or OAuth2 ``access_token``
* Download files for a project through a ``master_access_token`` or OAuth2 ``access_token``

Installation
============

You can install ``open-humans-api`` through ``pip``:

.. code-block:: Shell

  pip install open-humans-api

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   cli
   ohapi
   tests


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

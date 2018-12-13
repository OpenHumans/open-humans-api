Command Line Tools
******************


Example Use Cases
=================

Download public files for a given project/user
----------------------------------------------

You can use ``ohpub-download`` on the command line to download all public files
associated with a project. Here is an example that will download all public
23andMe files:

.. code-block:: Shell

  mkdir 23andme # create new folder to store the data in
  ohpub-download --source direct-sharing-128 --directory 23andme

To do the same for all public files of a given user:

.. code-block:: Shell

  mkdir gedankenstuecke # create new folder to store the data in
  ohpub-download --username gedankenstuecke --directory gedankenstuecke


Download private files from members of your project
---------------------------------------------------

If you are running a project yourself you can use a ``master_access_token``
you can get `from the Open Humans website <https://www.openhumans.org/direct-sharing/on-site-data-access/>`_
to download the files shared with you.

Here is an example of how to do this:

.. code-block:: Shell

  mkdir my_downloaded_data # create new folder to store the data in
  ohproj-download --master-token my_master_access_token --directory my_downloaded_data


Upload files to the accounts of your project members
----------------------------------------------------

Uploading data into your members accounts is two-step procedure using both
``ohproj-upload-metadata`` as well as ``ohproj-upload``, as you first need to draft
some metadata that will go along with the files.

Both commands expect a directory that contains sub-directories named after
your members ``project_member_id``. An example directory structure with files could look like this:

* member_data/

  * 01234567/

    * testdata.json
    * testdata.txt

  * 12345678/

    * testdata.json
    * testdata.txt

To upload this data we need to have a ``CSV`` file that contains the metadata.
We can draft one using the following command:


.. code-block:: Shell

  ohproj-upload-metadata -d member_data --create-csv member_data_metadata.csv

The resulting CSV will look like this:

.. code-block:: shell

  $ cat member_data_metadata.csv =>
  project_member_id,filename,tags,description,md5,creation_date
  01234567,testdata.txt,,,fa61a92e21a2597900cbde09d8ddbc1a,2016-08-23T15:23:22.277060+00:00
  01234567,testdata.json,json,,577da9879649acaf17226a6461bd19c8,2016-08-23T16:06:16.415039+00:00
  12345678,testdata.txt,,,fa61a92e21a2597900cbde09d8ddbc1a,2016-09-20T10:10:59.863201+00:00
  12345678,testdata.json,json,,577da9879649acaf17226a6461bd19c8,2016-09-20T10:10:59.859201+00:00

Edit this CSV with a text or spreadsheet editor of your choice to contain the metadata and then save it as a CSV again:

.. code-block:: shell

  $ cat member_data_metadata.csv =>
  project_member_id,filename,tags,description,md5,creation_date
  1234567,testdata.txt,"txt, verbose-data",Complete test data in text format.,fa61a92e21a2597900cbde09d8ddbc1a,2016-08-23T15:23:22.277060+00:00
  1234567,testdata.json,"json, metadata",Summary metadata in JSON format.,577da9879649acaf17226a6461bd19c8,2016-08-23T16:06:16.415039+00:00
  12345678,testdata.txt,"txt, verbose-data",Complete test data in text format.,fa61a92e21a2597900cbde09d8ddbc1a,2016-09-20T10:10:59.863201+00:00
  12345678,testdata.json,"json, metadata",Summary test data JSON.,577da9879649acaf17226a6461bd19c8,2016-09-20T10:10:59.859201+00:00

We filled in the tags as a ``"``-escaped and comma-separated list as well as a text-description.
With this we can now perform the actual upload like this:

.. code-block:: shell

  ohproj-upload -T YOUR_MASTER_ACCESS_TOKEN --metadata-csv member_data_metadata.csv -d member_data

This will upload the data from the ``member_data`` directory along with the metadata specified in ``member_data_metadata.csv``.

List of commands and their parameters
=====================================

.. click:: ohapi.command_line:public_data_download_cli
    :prog: ohpub-download

.. click:: ohapi.command_line:download_cli
    :prog: ohproj-download

.. click:: ohapi.command_line:download_metadata_cli
    :prog: ohproj-download-metadata

.. click:: ohapi.command_line:upload_metadata_cli
    :prog: ohproj-upload-metadata

.. click:: ohapi.command_line:upload_cli
    :prog: ohproj-upload

.. click:: ohapi.command_line:oauth_token_exchange_cli
    :prog: ohproj-oauth2-token-exchange

.. click:: ohapi.command_line:oauth2_auth_url_cli
    :prog: ohproj-oauth2-url

.. click:: ohapi.command_line:message_cli
    :prog: ohproj-message

.. click:: ohapi.command_line:delete_cli
    :prog: ohproj-delete

.. automodule:: ohapi.command_line
    :members:
    :undoc-members:
    :show-inheritance:

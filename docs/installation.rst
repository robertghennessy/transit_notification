.. highlight:: shell

============
Installation
============


Stable release
--------------

To install Transit notification, run this command in your terminal:

.. code-block:: console

    $ pip install transit_notification

This is the preferred method to install Transit notification, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for Transit notification can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/robertghennessy/transit_notification

Or download the `tarball`_:

.. code-block:: console

    $ curl -OJL https://github.com/robertghennessy/transit_notification/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/robertghennessy/transit_notification
.. _tarball: https://github.com/robertghennessy/transit_notification/tarball/master

API Key
-------

API key is required to connect with the server. San Francisco Bay Area 511.org API key can be requested
at https://511.org/open-data/token

.ENV File
---------

Rename env_template to .env and fill out the file with the required information.

lektor-tekir-admin
==================

lektor-tekir-admin is an alternative admin panel for `Lektor`_.
It doesn't modify existing behavior, but only adds new routes
for the new panel.

Features:

- Supports multiple languages (English and Turkish at the moment).

To use it, run::

  lektor-tekir serve

And then visit the URL "http://localhost:5000/admin-tekir/en/".

The ``lektor-tekir`` CLI is identical to the Lektor CLI
except that it patches the ``serve`` command to enable its own panel.

.. _Lektor: https://www.getlektor.com/

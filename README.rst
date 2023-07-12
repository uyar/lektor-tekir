lektor-tekir
============

lektor-tekir is an alternative admin panel for `Lektor`_.
It doesn't modify existing behavior, but only adds new routes
for the new panel.

What -sort of- works, hopefully:

- Navigating existing content.
- Editing existing content.
- Adding new content.
- Deleting content.
- Deleting attachments.
- Multiple language support in the UI (English and Turkish at the moment).
- Light/dark mode toggle.

What's planned in the short term:

- Adding attachments.
- Editing system fields.
- Dividing edit form fields into tabs.
- Deploying the site.
- Supporting Git.
- Managing content translations.
- TinyMCE, Quill or some other editor integration.

What's planned in the longer term:

- Managing databags.
- Markdown editor integration.
- Managing everything (templates, static assets, models, flow blocks, etc).

It can be installed using pip::

  pip install lektor-tekir

To use it, run::

  lektor-tekir serve

And then visit the URL "http://localhost:5000/tekir-admin/en/".

The ``lektor-tekir`` CLI is identical to the Lektor CLI
except that it patches the ``serve`` command to enable its own panel.

.. _Lektor: https://www.getlektor.com/

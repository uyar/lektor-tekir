lektor-tekir
============

lektor-tekir is an alternative admin panel for `Lektor`_.

What works:

- Navigating content.
- Adding, editing and deleting content items.
- Adding, deleting attachments.
- Publishing (deploying) the site.
- Multiple language support in the UI (English and Turkish at the moment).
- Light/dark mode toggle.

What's planned in the short term:

- Editing attachments.
- Editing system fields.
- Dividing edit form fields into tabs.
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

And use the edit buttons on pages.

The ``lektor-tekir`` CLI is identical to the Lektor CLI
except that it patches the ``serve`` command to enable its own panel.

.. _Lektor: https://www.getlektor.com/

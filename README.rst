lektor-tekir
============

lektor-tekir is an alternative admin panel for `Lektor`_.

What works:

- Navigating content.
- Adding, editing and deleting content items.
- Adding, deleting and replacing attachments.
- Publishing (deploying) the site.
- Multiple language support in the UI (English and Turkish at the moment).
- Support for light/dark mode preference.
- A widget for navigating content elements in the site.

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

All icons are from the Breeze project.

.. _Lektor: https://www.getlektor.com/

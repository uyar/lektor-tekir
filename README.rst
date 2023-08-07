lektor-tekir
============

lektor-tekir is an alternative admin panel for `Lektor`_.

Features:

- Navigating content.
- Adding, editing and deleting content items.
- Adding, deleting and replacing attachments.
- Managing content translations.
- Publishing (deploying) the site.
- Multiple language support in the UI (English and Turkish at the moment).
- Support for light/dark mode preference.
- A widget for navigating content elements in the site.

Planned:

- Editing attachments.
- Dividing edit form fields into tabs.
- Supporting Git.
- Managing databags.
- HTML editor integration.
- Image editor integration.
- Markdown editor integration.

It can be installed using pip::

  pip install lektor-tekir

To use it, run::

  lektor-tekir serve

And use the Lektor edit button as usual.

The ``lektor-tekir`` CLI is identical to the Lektor CLI
except that it patches the ``serve`` command to enable its own panel.

Acknowledgements
----------------

A big thank you to the following wonderful projects:

- `HTMX`_ for the JavaScript framework (license: BSD 2-Clause)
- `Breeze Icons`_ for the icons (license: GNU LGPL v3+)
- `SVG Loaders`_ for the button spinners (license: MIT)

And, goes without saying, to `Lektor`_ of course.

.. _Lektor: https://www.getlektor.com/
.. _HTMX: https://htmx.org/
.. _Breeze Icons: https://invent.kde.org/frameworks/breeze-icons
.. _SVG Loaders: https://samherbert.net/svg-loaders/

# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from pathlib import Path
from unittest.mock import patch

from flask import g
from flask_babel import Babel, get_locale
from lektor.admin.webui import WebUI
from lektor.cli import cli

from lektor_tekir import api, dash


class TekirAdminUI(WebUI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.register_blueprint(dash.bp)
        self.register_blueprint(api.bp)

        locale_dir = Path(__file__).parent / "translations"
        babel = Babel(self, locale_selector=lambda: g.lang_code,
                      default_translation_directories=str(locale_dir))
        self.jinja_env.globals["get_locale"] = get_locale
        self.jinja_env.globals["translations"] = babel.list_translations


def main():
    with patch("lektor.admin.WebAdmin", TekirAdminUI):
        cli()

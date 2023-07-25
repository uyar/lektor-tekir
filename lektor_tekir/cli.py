# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from pathlib import Path

from flask import g
from flask_babel import Babel
from lektor import admin
from lektor.admin.modules import serve
from lektor.admin.webui import WebUI
from lektor.cli import cli

from lektor_tekir import dash


class TekirAdminUI(WebUI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.register_blueprint(dash.make_blueprint())

        locale_dir = Path(__file__).parent / "translations"
        babel = Babel(self, locale_selector=lambda: g.lang_code,
                      default_domain="lektor_tekir",
                      default_translation_directories=str(locale_dir))
        self.jinja_env.globals["translations"] = babel.list_translations


rewrite_html_original = serve.rewrite_html_for_editing


def rewrite_html_tekir(fp, edit_url):
    tekir_url = edit_url.replace("/admin/edit", "/tekir-admin/en/contents")
    return rewrite_html_original(fp, tekir_url)


def main():
    admin.WebAdmin = TekirAdminUI
    serve.rewrite_html_for_editing = rewrite_html_tekir
    cli()

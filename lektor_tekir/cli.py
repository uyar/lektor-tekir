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
from lektor_tekir.utils import i18n_name


class TekirAdminUI(WebUI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tekir_admin = dash.make_blueprint()
        self.register_blueprint(tekir_admin)

        locale_dir = Path(__file__).parent / "translations"
        babel = Babel(self,
                      locale_selector=lambda: g.lang_code,
                      default_domain="lektor_tekir",
                      default_translation_directories=str(locale_dir))
        self.jinja_env.globals["i18n_name"] = i18n_name


rewrite_html_original = serve.rewrite_html_for_editing


def rewrite_html_tekir(fp, edit_url):
    tekir_url = edit_url.replace("/admin/edit", "/tekir-admin/en/contents")
    return rewrite_html_original(fp, tekir_url)


def main():
    # XXX: remove when Turkish translation is guaranteed to be installed
    import lektor
    turkish_dst = Path(lektor.__path__[0]) / "translations" / "tr.json"
    if not turkish_dst.exists():
        turkish_src = Path(__file__).parent / "static" / "tr.json"
        turkish_dst.write_bytes(turkish_src.read_bytes())

    admin.WebAdmin = TekirAdminUI
    serve.rewrite_html_for_editing = rewrite_html_tekir
    cli()

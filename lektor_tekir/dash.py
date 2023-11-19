# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, Response, current_app, g, render_template, request
from flask_babel import Babel

from . import api, utils


def preferences() -> str:
    babel: Babel = current_app.extensions["babel"].instance
    translations = babel.list_translations()
    return render_template("tekir_preferences.html", translations=translations)


def overview() -> str:
    return render_template("tekir_overview.html")


def contents() -> str | Response:
    record, status = utils.get_record(g.admin_context.pad, request.args)
    if record is None:
        return Response("", status=status)
    ancestors = utils.get_ancestors(record)
    template = "tekir_contents.html" if not record.is_attachment else \
        "tekir_attachment.html"
    return render_template(template, record=record, ancestors=ancestors)


def edit_content() -> str | Response:
    record, status = utils.get_record(g.admin_context.pad, request.args)
    if record is None:
        return Response("", status=status)
    system_fields = [record.datamodel.field_map[k]
                     for k in utils.SYSTEM_FIELDS]
    return render_template("tekir_content_edit.html", record=record,
                           system_fields=system_fields)


def make_blueprint() -> Blueprint:
    bp = Blueprint("tekir_admin",
                   __name__,
                   url_prefix="/tekir-admin/<lang_code>",
                   template_folder=Path(__file__).parent / "templates",
                   static_folder=Path(__file__).parent / "static")

    @bp.url_defaults
    def add_language_code(endpoint, values):
        values.setdefault("lang_code", g.lang_code)

    @bp.url_value_preprocessor
    def pull_language_code(endpoint, values):
        g.lang_code = values.pop("lang_code")

    bp.add_url_rule("/", view_func=overview)
    bp.add_url_rule("/preferences", view_func=preferences)
    bp.add_url_rule("/contents", view_func=contents)
    bp.add_url_rule("/content/edit", view_func=edit_content)

    tekir_api = api.make_blueprint()
    bp.register_blueprint(tekir_api)

    return bp

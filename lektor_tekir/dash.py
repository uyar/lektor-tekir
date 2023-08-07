# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path

from flask import Blueprint, Response, g, render_template, request
from lektor.constants import PRIMARY_ALT
from lektor.datamodel import Field
from lektor.db import Record

from . import api
from .utils import SYSTEM_FIELDS


def overview() -> str:
    return render_template("tekir_overview.html")


def contents() -> str | Response:
    path = request.args.get("path")
    if path is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    alt = request.args.get("alt", PRIMARY_ALT)
    record: Record = g.admin_context.pad.get(path, alt=alt)
    template = "tekir_contents.html" if not record.is_attachment else \
        "tekir_attachment.html"
    return render_template(template, record=record)


def edit_content() -> str | Response:
    path = request.args.get("path")
    if path is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    alt = request.args.get("alt", PRIMARY_ALT)
    record: Record = g.admin_context.pad.get(path, alt=alt)
    system_fields: list[Field] = [record.datamodel.field_map[k]
                                  for k in SYSTEM_FIELDS]
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
    bp.add_url_rule("/contents", view_func=contents)
    bp.add_url_rule("/content/edit", view_func=edit_content)

    tekir_api = api.make_blueprint()
    bp.register_blueprint(tekir_api)

    return bp

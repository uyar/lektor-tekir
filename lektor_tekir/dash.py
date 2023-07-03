# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from pathlib import Path

from flask import Blueprint, g, render_template, request


bp = Blueprint("admin_tekir", __name__, url_prefix="/admin-tekir/<lang_code>",
               template_folder=Path(__file__).parent / "templates",
               static_folder=Path(__file__).parent / "static")


@bp.url_defaults
def add_language_code(endpoint, values):
    values.setdefault("lang_code", g.lang_code)


@bp.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code = values.pop("lang_code")


@bp.route("/")
def summary():
    return render_template("tekir_summary.html")


@bp.route("/contents/")
def contents():
    path = request.args.get("path", "/")
    record = g.admin_context.tree.get(path)._primary_record
    parents = []
    current = record
    while current.parent:
        current = current.parent
        parents.append(current)
    parents.reverse()
    return render_template("tekir_contents.html", record=record,
                           parents=parents)


@bp.route("/content/edit")
def edit_content():
    path = request.args.get("path", "/")
    record = g.admin_context.tree.get(path)._primary_record
    return render_template("tekir_content_edit.html", record=record)

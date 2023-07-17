# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from datetime import datetime
from pathlib import Path

from flask import Blueprint, g, render_template, request
from flask_babel import gettext as _


bp = Blueprint("tekir_admin", __name__, url_prefix="/tekir-admin/<lang_code>",
               template_folder=Path(__file__).parent / "templates",
               static_folder=Path(__file__).parent / "static")


@bp.url_defaults
def add_language_code(endpoint, values):
    values.setdefault("lang_code", g.lang_code)


@bp.url_value_preprocessor
def pull_language_code(endpoint, values):
    g.lang_code = values.pop("lang_code")


@bp.route("/")
def summary():
    builder = g.admin_context.info.get_builder()
    output_path = Path(builder.destination_path)
    home_page = output_path / "index.html"
    if home_page.exists():
        mtime = int(home_page.stat().st_mtime)
        output_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
    else:
        output_time = _("No output")
    return render_template("tekir_summary.html", output_path=output_path,
                           output_time=output_time)


@bp.route("/contents")
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

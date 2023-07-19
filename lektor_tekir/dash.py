# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from datetime import datetime
from locale import strxfrm
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
    servers = g.admin_context.pad.config.get_servers()
    return render_template("tekir_summary.html", servers=servers,
                           output_path=output_path, output_time=output_time)


def get_ancestors(record):
    ancestors = []
    current = record
    while current.parent:
        current = current.parent
        ancestors.append(current)
    ancestors.reverse()
    return ancestors


@bp.route("/contents")
def contents():
    path = request.args.get("path", "/")
    record = g.admin_context.tree.get(path)._primary_record
    ancestors = get_ancestors(record)
    child_model_name = record.datamodel.child_config.model
    if child_model_name is not None:
        child_models = [record.pad.db.datamodels[child_model_name]]
    else:
        child_models = sorted(
            [m for m in record.pad.db.datamodels.values() if not m.hidden],
            key=lambda m: strxfrm(m.name_i18n.get(g.lang_code) or m.name)
        )
    return render_template("tekir_contents.html", record=record,
                           ancestors=ancestors, child_models=child_models)


@bp.route("/content/edit")
def edit_content():
    path = request.args.get("path", "/")
    record = g.admin_context.tree.get(path)._primary_record
    return render_template("tekir_content_edit.html", record=record)


@bp.route("/attachment/edit")
def edit_attachment():
    path = request.args.get("path", "/")
    record = g.admin_context.tree.get(path)._primary_record
    ancestors = get_ancestors(record)
    return render_template("tekir_attachment_edit.html", record=record,
                           ancestors=ancestors)

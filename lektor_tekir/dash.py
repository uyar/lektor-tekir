# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from datetime import datetime
from locale import strxfrm
from pathlib import Path

from flask import Blueprint, g, render_template, request
from flask_babel import gettext as _

from . import api, utils


def overview():
    builder = g.admin_context.info.get_builder()
    output_path = Path(builder.destination_path)
    home_page = output_path / "index.html"
    if home_page.exists():
        mtime = int(home_page.stat().st_mtime)
        output_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
    else:
        output_time = _("No output")
    servers = g.admin_context.pad.config.get_servers()
    return render_template("tekir_overview.html", servers=servers,
                           output_path=output_path, output_time=output_time)


def contents():
    path = request.args.get("path", "/")
    record = g.admin_context.tree.get(path)._primary_record
    ancestors = utils.get_ancestors(record)
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


def edit_content():
    path = request.args.get("path", "/")
    record = g.admin_context.tree.get(path)._primary_record
    return render_template("tekir_content_edit.html", record=record)


def edit_attachment():
    path = request.args.get("path", "/")
    record = g.admin_context.tree.get(path)._primary_record
    ancestors = utils.get_ancestors(record)
    return render_template("tekir_attachment_edit.html", record=record,
                           ancestors=ancestors)


def make_blueprint():
    bp = Blueprint("tekir_admin", __name__,
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
    bp.add_url_rule("/attachment/edit", view_func=edit_attachment)

    bp.register_blueprint(api.make_blueprint())

    return bp

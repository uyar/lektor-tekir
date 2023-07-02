# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from pathlib import Path

from flask import Blueprint, g, render_template, request
from flask_babel import gettext as _


MULTILINE = {"text", "strings", "markdown", "html", "rst"}


bp = Blueprint("admin_tekir_api", __name__, url_prefix="/admin-tekir/api")


@bp.route("/page-count")
def page_count():
    root_path = Path(g.admin_context.pad.env.root_path)
    pages = {c.parent for c in root_path.glob("**/contents*.lr")}
    return str(len(pages))


@bp.route("/subpages")
def subpages():
    g.lang_code = request.args.get("lang", "en")
    path = request.args.get("path")
    node = g.admin_context.tree.get(path)
    children = [c._primary_record for c in node.iter_subpages()]
    return render_template("tekir_subpages.html",
                           current=node._primary_record, records=children)


@bp.route("/attachments")
def attachments():
    g.lang_code = request.args.get("lang", "en")
    path = request.args.get("path")
    node = g.admin_context.tree.get(path)
    children = [c._primary_record for c in node.iter_attachments()]
    return render_template("tekir_attachments.html",
                           current=node._primary_record, records=children)


@bp.route("/save_content", methods=["POST"])
def save_content():
    g.lang_code = request.args.get("lang", "en")
    path = request.args.get("path")
    node = g.admin_context.tree.get(path)
    entries = []
    for field in node._primary_record.datamodel.fields:
        value = request.form.get(field.name)
        if value is not None:
            value = value.strip()
            if len(value) > 0:
                if field.type.name in MULTILINE:
                    entries.append(f"{field.name}:\n\n{value}")
                else:
                    entries.append(f"{field.name}: {value}")
    # print("\n---\n".join(entries))
    return _("Content saved.")

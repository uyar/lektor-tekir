# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektorly is released under the BSD license.
# Read the included LICENSE.txt file for details.

from pathlib import Path

from flask import Blueprint, g, request
from lektor.admin.modules.common import AdminContext
from lektor.db import TreeItem


bp = Blueprint("lektorly_api", __name__, url_prefix="/lektorly/api")


@bp.route("/page-count")
def page_count() -> str:
    context: AdminContext = g.admin_context
    root_path = Path(context.pad.env.root_path)
    pages = {c.parent for c in root_path.glob("**/contents*.lr")}
    return str(len(pages))


@bp.route("/subpages")
def subpages() -> str:
    path: str = request.args.get("path")
    context: AdminContext = g.admin_context
    page: TreeItem = context.tree.get(path)
    subpages = [f"<li>{c.path}</li>" for c in page.iter_subpages()]
    return "\n".join(subpages)


@bp.route("/attachments")
def attachments() -> str:
    path: str = request.args.get("path")
    context: AdminContext = g.admin_context
    page: TreeItem = context.tree.get(path)
    attachments = [f"<li>{c.path}</li>" for c in page.iter_attachments()]
    return "\n".join(attachments)

# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektorly is released under the BSD license.
# Read the included LICENSE.txt file for details.

from pathlib import Path
from typing import List

from flask import Blueprint, g, request
from lektor.db import Attachment, Page, TreeItem


bp = Blueprint("lektorly_api", __name__, url_prefix="/lektorly/api")


@bp.route("/page-count")
def page_count() -> str:
    root_path = Path(g.admin_context.pad.env.root_path)
    pages = {c.parent for c in root_path.glob("**/contents*.lr")}
    return str(len(pages))


@bp.route("/subpages")
def subpages() -> str:
    path: str = request.args.get("path")
    node: TreeItem = g.admin_context.tree.get(path)
    subs: List[Page] = [p._primary_record for p in node.iter_subpages()]
    markup = [f"<li>{c['title'] or c.path}</li>" for c in subs]
    return "\n".join(markup)


@bp.route("/attachments")
def attachments() -> str:
    path: str = request.args.get("path")
    node: TreeItem = g.admin_context.tree.get(path)
    subs: List[Attachment] = [a._primary_record
                              for a in node.iter_attachments()]
    markup = [f"<li>{node._primary_record.url_to(c)}</li>" for c in subs]
    return "\n".join(markup)

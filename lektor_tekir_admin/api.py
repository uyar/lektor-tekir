# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir-admin is released under the BSD license.
# Read the included LICENSE.txt file for details.

from pathlib import Path
from typing import List

from flask import Blueprint, g, request, url_for
from lektor.db import TreeItem


LINKED_LISTITEM = """<li><a href="%(url)s">%(title)s</a></li>"""


bp = Blueprint("admin_tekir_api", __name__, url_prefix="/admin-tekir/api")


@bp.route("/page-count")
def page_count() -> str:
    root_path = Path(g.admin_context.pad.env.root_path)
    pages = {c.parent for c in root_path.glob("**/contents*.lr")}
    return str(len(pages))


@bp.route("/subpages")
def subpages() -> str:
    g.lang_code = request.args.get("lang", "en")
    path: str = request.args.get("path")
    node: TreeItem = g.admin_context.tree.get(path)
    items: List[str] = [
        LINKED_LISTITEM % {
            "url": url_for("admin_tekir.contents", path=c.path),
            "title": c["title"],
        }
        for c in [p._primary_record for p in node.iter_subpages()]
    ]
    return "\n".join(items)


@bp.route("/attachments")
def attachments() -> str:
    g.lang_code = request.args.get("lang", "en")
    path: str = request.args.get("path")
    node: TreeItem = g.admin_context.tree.get(path)
    items: List[str] = [
        LINKED_LISTITEM % {
            "url": url_for("admin_tekir.contents", path=c.path),
            "title": node._primary_record.url_to(c),
        }
        for c in [p._primary_record for p in node.iter_attachments()]
    ]
    return "\n".join(items)

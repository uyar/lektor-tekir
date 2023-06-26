# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektorly is released under the BSD license.
# Read the included LICENSE.txt file for details.

from pathlib import Path

from flask import Blueprint, g
from lektor.admin.modules.common import AdminContext


bp = Blueprint("lektorly_api", __name__, url_prefix="/lektorly/api")


def get_page_count(root: Path) -> int:
    pages = {c.parent for c in root.glob("**/contents*.lr")}
    return len(pages)


@bp.route("/page-count")
def page_count() -> str:
    context: AdminContext = g.admin_context
    root_path = Path(context.pad.env.root_path)
    return str(get_page_count(root_path))

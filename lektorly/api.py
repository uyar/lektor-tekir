# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektorly is released under the BSD license.
# Read the included LICENSE.txt file for details.

from typing import List

from flask import Blueprint, g
from lektor import db


bp = Blueprint("lektorly_api", __name__, url_prefix="/lektorly/api")


def get_subpages(node: db.TreeItem) -> List[db.TreeItem]:
    subpages: List[db.TreeItem] = list(node.iter_subpages())
    descendants: List[db.TreeItem] = []
    for subpage in subpages:
        descendants.extend(get_subpages(subpage))
    return subpages + descendants


def get_subpage_count(node: db.TreeItem) -> int:
    subpages: List[db.TreeItem] = list(node.iter_subpages())
    n_subpages = 0
    for subpage in subpages:
        n_subpages += get_subpage_count(subpage)
    return n_subpages + len(subpages)


@bp.route("/page-count")
def get_page_count() -> str:
    root: db.TreeItem = g.admin_context.tree.get("/")
    return str(get_subpage_count(root))

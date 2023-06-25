# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektorly is released under the BSD license.
# Read the included LICENSE.txt file for details.

from flask import Blueprint, g


bp = Blueprint("lektorly_api", __name__, url_prefix="/lektorly/api")


def get_subpages(node):
    subpages = list(node.iter_subpages())
    descendants = []
    for subpage in subpages:
        descendants.extend(get_subpages(subpage))
    return subpages + descendants


def get_subpage_count(node):
    subpages = list(node.iter_subpages())
    n_subpages = 0
    for subpage in subpages:
        n_subpages += get_subpage_count(subpage)
    return n_subpages + len(subpages)


@bp.route("/pagecount")
def get_page_count():
    root = g.admin_context.tree.get("/")
    return str(get_subpage_count(root))

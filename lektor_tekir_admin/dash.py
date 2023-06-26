# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir-admin is released under the BSD license.
# Read the included LICENSE.txt file for details.

from pathlib import Path

from flask import Blueprint, render_template


bp = Blueprint("admin_tekir", __name__, url_prefix="/admin_tekir",
               template_folder=Path(__file__).parent / "templates",
               static_folder=Path(__file__).parent / "static")


@bp.route("/")
def dashboard():
    return render_template("tekir_dashboard.html")


@bp.route("/contents")
def contents():
    return render_template("tekir_contents.html")

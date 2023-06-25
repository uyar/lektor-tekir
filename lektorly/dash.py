# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektorly is released under the BSD license.
# Read the included LICENSE.txt file for details.

from pathlib import Path

from flask import Blueprint, render_template


bp = Blueprint("lektorly", __name__, url_prefix="/lektorly",
               template_folder=Path(__file__).parent / "templates",
               static_folder=Path(__file__).parent / "static")


@bp.route("/")
def dashboard():
    return render_template("lektorly_dashboard.html")

# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektorly is released under the BSD license.
# Read the included LICENSE.txt file for details.

from unittest.mock import patch

from lektor.admin.webui import WebUI
from lektor.cli import cli

from lektorly import dash


class LektorlyUI(WebUI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_blueprint(dash.bp)


def main():
    with patch("lektor.admin.WebAdmin", LektorlyUI):
        cli()

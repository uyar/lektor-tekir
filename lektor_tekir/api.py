# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from flask import Blueprint, Response, g, render_template, request, url_for
from flask_babel import format_datetime
from flask_babel import gettext as _
from lektor.builder import Builder
from lektor.db import Pad, Record
from lektor.environment.config import ServerInfo
from lektor.publisher import publish
from lektor.types.flow import FlowBlock
from slugify import slugify
from werkzeug.datastructures.file_storage import FileStorage

from . import utils


FILE_MANAGERS: dict[str, str] = {
    "darwin": "open",
    "linux": "xdg-open",
    "win32": "explorer",
}


def open_folder() -> str | Response:
    fs_path: str | None = request.args.get("fs_path")
    if fs_path is None:
        path: str | None = request.args.get("path")
        if path is None:
            return Response("", status=HTTPStatus.BAD_REQUEST)
        record: Record = g.admin_context.tree.get(path)._primary_record
        fs_path = str(Path(record.source_filename).parent)
    file_manager: str = FILE_MANAGERS.get(sys.platform, "xdg-open")
    subprocess.run([file_manager, fs_path])
    return ""


def clean_build() -> str:
    builder: Builder = g.admin_context.info.get_builder()
    builder.prune(all=True)
    builder.touch_site_config()
    return _("No output")


def build() -> str:
    builder: Builder = g.admin_context.info.get_builder()
    builder.build_all()
    builder.touch_site_config()
    output_time: datetime | None = utils.get_output_time(builder)
    if output_time is None:
        return _("No output")
    return format_datetime(output_time)


def publish_build() -> str | Response:
    server_id: str | None = request.form.get("server")
    if server_id is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    pad: Pad = g.admin_context.pad
    server_info: ServerInfo = pad.config.get_server(server_id)
    builder: Builder = g.admin_context.info.get_builder()
    event_iter: Iterable[str] = publish(pad.env,
                                        server_info.target,
                                        builder.destination_path,
                                        server_info=server_info)
    for line in event_iter:
        print(line)
    return ""


def check_delete() -> str:
    items: list[str] = request.form.getlist("selected-items")
    records: list[Record] = [g.admin_context.tree.get(i)._primary_record
                             for i in items]
    root: Record = g.admin_context.pad.root
    paths: list[str] = utils.get_record_paths(records, root=root)
    paths.sort()
    return "\n".join(f'<li>{p}</li>' for p in paths)


def delete_content() -> str:
    items: list[str] = request.form.getlist("selected-items")
    records: list[Record] = [g.admin_context.tree.get(i)._primary_record
                             for i in items]
    for record in records:
        utils.delete_record(record)
    return _("Deleted.")


def slug_from_title() -> Response:
    title: str | None = request.args.get("title")
    if title is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    slug: str = slugify(title)
    response = Response(slug)
    response.headers["HX-Trigger"] = '{"updateSlug": {"slug": "%s"}}' % slug
    return response


def new_subpage() -> str | Response:
    parent: str | None = request.args.get("parent")
    model: str | None = request.form.get("model")
    if (parent is None) or (model is None):
        return Response("", status=HTTPStatus.BAD_REQUEST)

    title: str = request.form.get("title", "").strip()
    if title == "":
        return _("Every content item must have a title.")

    try:
        path: str = utils.create_subpage(
            pad=g.admin_context.pad,
            parent=parent,
            model=model,
            title=title,
            form=request.form,
        )
    except ValueError:
        return _("A content item with this name already exists.")

    response = Response(_("Added."))
    record_url = url_for("tekir_admin.edit_content", path=path)
    response.headers["HX-Redirect"] = record_url
    return response


def new_attachment() -> str | Response:
    uploaded: FileStorage | None = request.files.get("file")
    if not uploaded:
        return _("Please upload a file.")

    parent: str | None = request.args.get("path")
    if parent is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)

    try:
        path: str = utils.create_attachment(
            pad=g.admin_context.pad,
            parent=g.admin_context.tree.get(parent)._primary_record,
            uploaded=uploaded,
        )
    except ValueError:
        return _("An attachment with this name already exists for this item.")

    response = Response(_("Added."))
    record_url = url_for("tekir_admin.edit_attachment", path=path)
    response.headers["HX-Redirect"] = record_url
    return response


def check_changes() -> Response:
    path: str | None = request.args.get("path")
    if path is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    record: Record = g.admin_context.tree.get(path)._primary_record
    record_url: str = url_for("tekir_admin.contents", path=record.path)
    content: str = utils.get_content(record, request.form)
    source = Path(record.source_filename)
    if content == source.read_text():
        response = Response("")
        response.headers["HX-Redirect"] = record_url
    else:
        message = _("There are unsaved changes. Do you want to continue?")
        trigger = '{"showChanges": {"href": "%s"}}' % record_url
        response = Response(message)
        response.headers["HX-Trigger"] = trigger
    return response


def save_content() -> str | Response:
    path: str | None = request.args.get("path")
    if path is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    record: Record = g.admin_context.tree.get(path)._primary_record
    content: str = utils.get_content(record, request.form)
    source = Path(record.source_filename)
    if content == source.read_text():
        return _("No changes.")
    else:
        source.write_text(content)
        return _("Content saved.")


def replace_attachment() -> str | Response:
    uploaded: FileStorage | None = request.files.get("file")
    if not uploaded:
        return _("Please upload a file.")
    path: str | None = request.args.get("path")
    if path is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    pad: Pad = g.admin_context.pad
    source_path = Path(pad.db.to_fs_path(path))
    uploaded.save(source_path)
    response = Response("")
    record_url: str = url_for("tekir_admin.edit_attachment", path=path)
    response.headers["HX-Redirect"] = record_url
    return response


def new_flowblock() -> str | Response:
    path: str | None = request.args.get("path")
    field_name: str | None = request.args.get("field_name")
    flow_type: str | None = request.args.get("flow_type")
    if (path is None) or (field_name is None) or (flow_type is None):
        return Response("", status=HTTPStatus.BAD_REQUEST)
    record: Record = g.admin_context.tree.get(path)._primary_record
    block: FlowBlock = utils.create_flowblock(record=record,
                                              flow_type=flow_type)
    uuid_index: str = uuid4().hex
    return render_template("tekir_flowblock.html", block=block,
                           field_name=field_name,
                           block_index=f"uuid_{uuid_index}")


def navigables():
    path = request.args.get("path")
    record = g.admin_context.tree.get(path)._primary_record
    options = [("", "----", "selected" if not path else "")]
    options.append(("/", _("home"), "selected" if path == "/" else ""))
    if path and (path != "/"):
        options.append((record.path, record["_slug"], "selected"))
    for child in record.children:
        options.append((child.path, child["_slug"], ""))
    return "\n".join(f'<option value="{value}" {selected}>{label}</option>'
                     for value, label, selected in options)


def make_blueprint():
    bp = Blueprint("api", __name__, url_prefix="/api")

    bp.add_url_rule("/open-folder", view_func=open_folder)
    bp.add_url_rule("/clean-build", view_func=clean_build)
    bp.add_url_rule("/build", view_func=build)
    bp.add_url_rule("/publish-build", view_func=publish_build,
                    methods=["POST"])
    bp.add_url_rule("/check-delete", view_func=check_delete,
                    methods=["POST"])
    bp.add_url_rule("/delete-content", view_func=delete_content,
                    methods=["POST"])
    bp.add_url_rule("/slugify", view_func=slug_from_title)
    bp.add_url_rule("/new-content", view_func=new_subpage,
                    methods=["POST"])
    bp.add_url_rule("/new-attachment", view_func=new_attachment,
                    methods=["POST"])
    bp.add_url_rule("/check-changes", view_func=check_changes,
                    methods=["POST"])
    bp.add_url_rule("/save-content", view_func=save_content,
                    methods=["POST"])
    bp.add_url_rule("/replace-attachment", view_func=replace_attachment,
                    methods=["POST"])
    bp.add_url_rule("/new-flowblock", view_func=new_flowblock)
    bp.add_url_rule("/navigables", view_func=navigables)

    return bp

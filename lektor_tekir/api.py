# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from http import HTTPStatus
from locale import strxfrm
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from flask import Blueprint, Response, g, render_template, request, url_for
from flask_babel import format_datetime
from flask_babel import gettext as _
from lektor.builder import Builder
from lektor.constants import PRIMARY_ALT
from lektor.datamodel import DataModel
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


def i18n_name(item: DataModel) -> str:
    return strxfrm(item.name_i18n.get(g.lang_code, item.name))


def error_response(errors: list[str]) -> Response:
    markup: str = render_template("partials/error-dialog.html", errors=errors)
    response = Response(markup)
    response.headers["HX-Retarget"] = "#error-dialog"
    response.headers["HX-Reswap"] = "innerHTML"
    trigger = '{"showModal": {"modal": "#error-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def open_folder() -> Response:
    fs_path: str | None = request.args.get("fs_path")
    if fs_path is None:
        path: str | None = request.args.get("path")
        if path is None:
            return Response("", status=HTTPStatus.BAD_REQUEST)
        record: Record = g.admin_context.pad.get(path, alt=PRIMARY_ALT)
        fs_path = str(Path(record.source_filename).parent)

    file_manager: str = FILE_MANAGERS.get(sys.platform, "xdg-open")
    try:
        subprocess.run([file_manager, fs_path])
    except Exception as e:
        errors = [str(e)]
        return error_response(errors)
    return Response("")


def site_summary() -> str:
    root: Record = g.admin_context.pad.root
    page_count: int = utils.get_page_count(root)
    return render_template("partials/site-summary.html", page_count=page_count)


def site_output() -> str:
    builder: Builder = g.admin_context.info.get_builder()
    output: dict[str, str] = {"path": builder.destination_path}
    output_time: datetime | None = utils.get_output_time(builder)
    if output_time is None:
        output["time"] = _("No output")
    else:
        output["time"] = format_datetime(output_time)
    return render_template("partials/site-output.html", output=output)


def clean_build() -> str:
    builder: Builder = g.admin_context.info.get_builder()
    builder.prune(all=True)
    builder.touch_site_config()
    return _("No output")


def build() -> str | Response:
    builder: Builder = g.admin_context.info.get_builder()
    n_failures: int = builder.build_all()
    if n_failures > 0:
        errors = []
        for failure in Path(builder.failure_controller.path).glob("*.json"):
            error: dict[str, str] = json.loads(failure.read_text())
            errors.append(f'{error["artifact"]}: {error["exception"]}')
        return error_response(errors)
    builder.touch_site_config()
    output_time: datetime | None = utils.get_output_time(builder)
    if output_time is None:
        return _("No output")
    return format_datetime(output_time)


def publish_info() -> Response:
    servers: list[ServerInfo] = g.admin_context.pad.config.get_servers()
    markup: str = render_template("partials/publish-dialog.html",
                                  servers=servers)
    response = Response(markup)
    trigger = '{"showModal": {"modal": "#publish-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


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
    event_lines: list[str] = []
    for line in event_iter:
        event_lines.append(line)
    content = "\n".join(event_lines)
    return content


def content_summary() -> str | Response:
    path: str | None = request.args.get("path")
    if path is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    record: Record = g.admin_context.pad.get(path, alt=PRIMARY_ALT)
    ancestors: list[Record] = utils.get_ancestors(record)
    template = "content-summary.html" if not record.is_attachment else \
        "attachment-summary.html"
    return render_template(f"partials/{template}", record=record,
                           ancestors=ancestors)


def content_subpages() -> str | Response:
    path: str | None = request.args.get("path")
    if path is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    record: Record = g.admin_context.pad.get(path, alt=PRIMARY_ALT)
    subpages = sorted(record.children, key=lambda s: s["_slug"])
    return render_template("partials/content-subpages.html", record=record,
                           subpages=subpages)


def content_attachments() -> str | Response:
    path: str | None = request.args.get("path")
    if path is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    record: Record = g.admin_context.pad.get(path, alt=PRIMARY_ALT)
    attachments = sorted(record.attachments, key=lambda s: s["_slug"])
    return render_template("partials/content-attachments.html", record=record,
                           attachments=attachments)


def delete_collect() -> Response:
    items: list[str] = request.form.getlist("selected-items")
    form_id: str | None = request.form.get("form_id")
    if form_id is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    records: list[Record] = [g.admin_context.pad.get(i, alt=PRIMARY_ALT)
                             for i in items]
    root: Record = g.admin_context.pad.root
    paths: list[str] = utils.get_record_paths(records, root=root)
    markup: str = render_template("partials/delete-dialog.html",
                                  items=sorted(paths), form_id=form_id)
    response = Response(markup)
    trigger = '{"showModal": {"modal": "#delete-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def delete_content() -> Response:
    items: list[str] = request.form.getlist("selected-items")
    form_id: str | None = request.form.get("form_id")
    if form_id is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    records: list[Record] = [g.admin_context.pad.get(i, alt=PRIMARY_ALT)
                             for i in items]
    for record in records:
        utils.delete_record(record)
    response = Response("")
    detail = '{"form": "%(form)s", "modal": "%(modal)s"}' % {
        "form": f"#{form_id}",
        "modal": "#delete-dialog",
    }
    trigger = '{"deleteCheckedRows": %(detail)s}' % {"detail": detail}
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def slug_from_title() -> Response:
    title: str | None = request.args.get("title")
    if title is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    slug: str = slugify(title)
    response = Response(slug)
    detail = '{"target": "%(sel)s", "attr": "%(att)s", "value": "%(val)s"}' % {
        "sel": "#field-slug",
        "att": "placeholder",
        "val": slug,
    }
    trigger = '{"updateAttr": %(detail)s}' % {"detail": detail}
    response.headers["HX-Trigger"] = trigger
    return response


def new_subpage() -> Response:
    path: str | None = request.args.get("path")
    if path is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    record: Record = g.admin_context.pad.get(path, alt=PRIMARY_ALT)
    child_models: list[DataModel] = utils.get_child_models(record)
    models: list[DataModel] = sorted(child_models, key=i18n_name)
    markup: str = render_template("partials/new-subpage-dialog.html",
                                  record=record, models=models)
    response = Response(markup)
    trigger = '{"showModal": {"modal": "#new-subpage-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def add_subpage() -> Response:
    parent: str | None = request.args.get("parent")
    model: str | None = request.form.get("model")
    if (parent is None) or (model is None):
        return Response("", status=HTTPStatus.BAD_REQUEST)

    title: str = request.form.get("title", "").strip()
    if title == "":
        errors = [_("Every content item must have a title.")]
        return error_response(errors)

    try:
        path: str = utils.create_subpage(
            pad=g.admin_context.pad,
            parent=parent,
            model=model,
            title=title,
            form=request.form,
        )
    except FileExistsError:
        errors = [_("A content item with this name already exists.")]
        return error_response(errors)

    response = Response("")
    record_url = url_for("tekir_admin.edit_content", path=path)
    response.headers["HX-Redirect"] = record_url
    return response


def upload_attachment() -> Response:
    path: str | None = request.args.get("path")
    endpoint: str | None = request.args.get("op")
    if (path is None) or (endpoint is None):
        return Response("", status=HTTPStatus.BAD_REQUEST)
    record: Record = g.admin_context.pad.get(path, alt=PRIMARY_ALT)
    markup: str = render_template("partials/upload-dialog.html",
                                  record=record, endpoint=endpoint)
    response = Response(markup)
    trigger = '{"showModal": {"modal": "#upload-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def add_attachment() -> Response:
    parent: str | None = request.args.get("path")
    if parent is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)

    uploaded: FileStorage | None = request.files.get("file")
    if not uploaded:
        errors = [_("Please upload a file.")]
        return error_response(errors)

    try:
        path: str = utils.create_attachment(
            pad=g.admin_context.pad,
            parent=g.admin_context.pad.get(parent, alt=PRIMARY_ALT),
            uploaded=uploaded,
        )
    except FileExistsError:
        errors = [_("An attachment with this name already exists.")]
        return error_response(errors)

    response = Response()
    record_url: str = url_for("tekir_admin.contents", path=path)
    response.headers["HX-Redirect"] = record_url
    return response


def replace_attachment() -> Response:
    path: str | None = request.args.get("path")
    if path is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)

    uploaded: FileStorage | None = request.files.get("file")
    if not uploaded:
        errors = [_("Please upload a file.")]
        return error_response(errors)

    pad: Pad = g.admin_context.pad
    source_path = Path(pad.db.to_fs_path(path))
    uploaded.save(source_path)

    response = Response("")
    record_url: str = url_for("tekir_admin.contents", path=path)
    response.headers["HX-Redirect"] = record_url
    return response


def save_content() -> Response:
    path: str | None = request.args.get("path")
    if path is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)

    record: Record = g.admin_context.pad.get(path, alt=PRIMARY_ALT)
    content: str = utils.get_content(record, request.form)
    source = Path(record.source_filename)
    if content == source.read_text():
        message = _("No changes.")
    else:
        source.write_text(content)
        message = _("Content saved.")

    markup: str = render_template("partials/save-dialog.html",
                                  message=message, record=record)
    response = Response(markup)
    trigger = '{"showModal": {"modal": "#save-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def check_changes() -> Response:
    path: str | None = request.args.get("path")
    if path is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)

    record: Record = g.admin_context.pad.get(path, alt=PRIMARY_ALT)
    record_url: str = url_for("tekir_admin.contents", path=record.path)
    content: str = utils.get_content(record, request.form)
    source = Path(record.source_filename)
    if content == source.read_text():
        response = Response("")
        response.headers["HX-Redirect"] = record_url
    else:
        message = _("There are unsaved changes. Do you want to continue?")
        markup: str = render_template("partials/changes-dialog.html",
                                      message=message, record_url=record_url)
        response = Response(markup)
        trigger = '{"showModal": {"modal": "#changes-dialog"}}'
        response.headers["HX-Trigger-After-Swap"] = trigger
        response.headers["HX-Trigger"] = trigger
    return response


def new_flowblock() -> str | Response:
    path: str | None = request.args.get("path")
    field_name: str | None = request.args.get("field_name")
    flow_type: str | None = request.args.get("flow_type")
    if (path is None) or (field_name is None) or (flow_type is None):
        return Response("", status=HTTPStatus.BAD_REQUEST)
    record: Record = g.admin_context.pad.get(path, alt=PRIMARY_ALT)
    block: FlowBlock = utils.create_flowblock(record=record,
                                              flow_type=flow_type)
    uuid_index: str = uuid4().hex
    return render_template("tekir_flowblock.html", block=block,
                           field_name=field_name,
                           block_index=f"uuid_{uuid_index}")


def start_navigate() -> str | Response:
    field_id = request.args.get("field_id")
    if field_id is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)

    path: str = request.args.get("path", "/")
    record: Record = g.admin_context.pad.get(path, alt=PRIMARY_ALT)
    if record is None:
        record = g.admin_context.pad.root

    navigables: list[tuple[str, str, bool]] = utils.get_navigables(record)
    markup: str = render_template("partials/navigate-dialog.html",
                                  navigables=navigables, field_id=field_id)
    response = Response(markup)
    trigger = '{"showModal": {"modal": "#navigate-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def navigables() -> str | Response:
    path: str | None = request.args.get("path")
    if path is None:
        return Response("", status=HTTPStatus.BAD_REQUEST)
    record: Record = g.admin_context.pad.get(path, alt=PRIMARY_ALT)

    navigables: list[tuple[str, str, bool]] = utils.get_navigables(record)
    return render_template("partials/navigables.html",
                           navigables=navigables)


def make_blueprint():
    bp = Blueprint("api", __name__, url_prefix="/api")

    bp.add_url_rule("/open-folder", view_func=open_folder)

    bp.add_url_rule("/site-summary", view_func=site_summary)
    bp.add_url_rule("/site-output", view_func=site_output)
    bp.add_url_rule("/clean-build", view_func=clean_build)
    bp.add_url_rule("/build", view_func=build)
    bp.add_url_rule("/publish-info", view_func=publish_info)
    bp.add_url_rule("/publish-build", view_func=publish_build,
                    methods=["POST"])

    bp.add_url_rule("/content-summary", view_func=content_summary)
    bp.add_url_rule("/content-subpages", view_func=content_subpages)
    bp.add_url_rule("/content-attachments", view_func=content_attachments)
    bp.add_url_rule("/delete-collect", view_func=delete_collect,
                    methods=["POST"])
    bp.add_url_rule("/delete-content", view_func=delete_content,
                    methods=["POST"])
    bp.add_url_rule("/slugify", view_func=slug_from_title)
    bp.add_url_rule("/new-subpage", view_func=new_subpage)
    bp.add_url_rule("/add-subpage", view_func=add_subpage,
                    methods=["POST"])
    bp.add_url_rule("/upload-attachment", view_func=upload_attachment)
    bp.add_url_rule("/add-attachment", view_func=add_attachment,
                    methods=["POST"])

    bp.add_url_rule("/save-content", view_func=save_content,
                    methods=["POST"])
    bp.add_url_rule("/check-changes", view_func=check_changes,
                    methods=["POST"])
    bp.add_url_rule("/replace-attachment", view_func=replace_attachment,
                    methods=["POST"])
    bp.add_url_rule("/new-flowblock", view_func=new_flowblock)

    bp.add_url_rule("/start-navigate", view_func=start_navigate)
    bp.add_url_rule("/navigables", view_func=navigables)

    return bp

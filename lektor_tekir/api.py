# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from __future__ import annotations

import json
import subprocess
import sys
from http import HTTPStatus
from locale import strxfrm
from pathlib import Path
from typing import Iterable, Mapping
from uuid import uuid4

from flask import Blueprint, Response, g, render_template, request, url_for
from flask_babel import format_datetime
from flask_babel import gettext as _
from lektor.builder import Builder
from lektor.constants import PRIMARY_ALT
from lektor.datamodel import DataModel
from lektor.db import Pad, Query, Record, TreeItem
from lektor.environment.config import ServerInfo
from lektor.publisher import publish
from slugify import slugify

from . import utils


FILE_MANAGERS: dict[str, str] = {
    "darwin": "open",
    "linux": "xdg-open",
    "win32": "explorer",
}


def i18n_name(item: DataModel) -> str:
    return strxfrm(item.name_i18n.get(g.lang_code, item.name))


def error_response(errors: list[str]) -> Response:
    markup = render_template("partials/error-dialog.html", errors=errors)
    response = Response(markup)
    response.headers["HX-Retarget"] = "#error-dialog"
    response.headers["HX-Reswap"] = "innerHTML"
    trigger = '{"showModal": {"modal": "#error-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def _record(pad: Pad, args: Mapping[str, str], *,
            alt: str | None = None) -> tuple[Record | None, HTTPStatus]:
    record_path = args.get("path")
    if record_path is None:
        return (None, HTTPStatus.UNPROCESSABLE_ENTITY)
    if (alt is not None) and ("alt" in args):
        return (None, HTTPStatus.UNPROCESSABLE_ENTITY)
    record_alt = alt if alt is not None else args.get("alt", PRIMARY_ALT)
    record: Record = pad.get(record_path, alt=record_alt)
    if record is None:
        return (None, HTTPStatus.NOT_FOUND)
    return (record, HTTPStatus.OK)


def open_folder() -> Response:
    file_manager = FILE_MANAGERS.get(sys.platform)
    if file_manager is None:
        error = _("File manager not set for platform:") + f" '{sys.platform}'"
        return error_response([error])

    folder = request.args.get("folder")
    if folder is not None:
        fs_path = Path(folder)
    else:
        record, status = _record(g.admin_context.pad, request.args,
                                 alt=PRIMARY_ALT)
        if record is None:
            return Response("", status=status)
        fs_path = Path(record.source_filename).parent
    if not fs_path.exists():
        return Response("", status=HTTPStatus.NOT_FOUND)

    try:
        subprocess.run([file_manager, fs_path])
    except Exception as e:
        errors = [str(e)]
        return error_response(errors)
    return Response("")


def site_summary() -> str:
    root: Record = g.admin_context.pad.root
    page_count = utils.get_page_count(root)
    return render_template("partials/site-summary.html", page_count=page_count)


def site_output() -> str:
    builder: Builder = g.admin_context.info.get_builder()
    output = {"path": builder.destination_path}
    output_time = utils.get_output_time(builder)
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
    n_failures = builder.build_all()
    if n_failures > 0:
        errors = []
        for failure in Path(builder.failure_controller.path).glob("*.json"):
            error: dict[str, str] = json.loads(failure.read_text())
            errors.append(f'{error["artifact"]}: {error["exception"]}')
        return error_response(errors)
    builder.touch_site_config()
    output_time = utils.get_output_time(builder)
    if output_time is None:
        return _("No output")
    return format_datetime(output_time)


def publish_info() -> Response:
    servers: list[ServerInfo] = g.admin_context.pad.config.get_servers()
    markup = render_template("partials/publish-dialog.html", servers=servers)
    response = Response(markup)
    trigger = '{"showModal": {"modal": "#publish-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def publish_build() -> str | Response:
    server_id = request.form.get("server")
    if server_id is None:
        return Response("", status=HTTPStatus.UNPROCESSABLE_ENTITY)

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
    record, status = _record(g.admin_context.pad, request.args)
    if record is None:
        return Response("", status=status)
    ancestors = utils.get_ancestors(record)
    template = "content-summary.html" if not record.is_attachment else \
        "attachment-summary.html"
    return render_template(f"partials/{template}", record=record,
                           ancestors=ancestors)


def content_translations() -> str | Response:
    record, status = _record(g.admin_context.pad, request.args)
    if record is None:
        return Response("", status=status)
    node: TreeItem = g.admin_context.tree.get(record.path)
    return render_template("partials/content-translations.html", record=record,
                           alts=node.alts)


def content_subpages() -> str | Response:
    record, status = _record(g.admin_context.pad, request.args)
    if record is None:
        return Response("", status=status)
    children: Query = record.children.include_hidden(True) \
                                     .include_undiscoverable(True)
    if children.get_order_by() is None:
        children = children.order_by("_slug")
    return render_template("partials/content-subpages.html", record=record,
                           subpages=children)


def content_attachments() -> str | Response:
    record, status = _record(g.admin_context.pad, request.args)
    if record is None:
        return Response("", status=status)
    children: Query = record.attachments.include_hidden(True) \
                                        .include_undiscoverable(True)
    if children.get_order_by() is None:
        children = children.order_by("_slug")
    return render_template("partials/content-attachments.html", record=record,
                           attachments=children)


def delete_confirm() -> Response:
    form_id = request.form.get("form_id")
    if form_id is None:
        return Response("", status=HTTPStatus.UNPROCESSABLE_ENTITY)

    items = request.form.getlist("selected-items")
    pad: Pad = g.admin_context.pad
    records: list[Record] = [pad.get(i, alt=PRIMARY_ALT) for i in items]
    paths = utils.get_record_paths(records, root=pad.root)
    markup = render_template("partials/delete-dialog.html",
                             items=sorted(paths), form_id=form_id)
    response = Response(markup)
    trigger = '{"showModal": {"modal": "#delete-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def delete_translation_confirm() -> Response:
    path = request.args.get("path")
    alt = request.args.get("alt")
    if (path is None) or (alt is None) or (alt == PRIMARY_ALT):
        return Response("", status=HTTPStatus.UNPROCESSABLE_ENTITY)

    pad: Pad = g.admin_context.pad
    record: Record = pad.get(path, alt=alt)
    root: Record = pad.root
    root_dir = Path(root.source_filename).parent
    item = Path(record.source_filename).relative_to(root_dir)
    vals = '{"path": "%(path)s", "alt": "%(alt)s"}' % {
        "path": record.path,
        "alt": record.alt,
    }
    markup = render_template("partials/delete-dialog.html", items=[item],
                             vals=vals)
    response = Response(markup)
    trigger = '{"showModal": {"modal": "#delete-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def delete_content() -> Response:
    items = request.form.getlist("selected-items")
    form_id = request.form.get("form_id")
    if form_id is None:
        return Response("", status=HTTPStatus.UNPROCESSABLE_ENTITY)

    pad: Pad = g.admin_context.pad
    records: list[Record] = [pad.get(i, alt=PRIMARY_ALT) for i in items]
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


def delete_translation() -> str | Response:
    path = request.args.get("path")
    alt = request.args.get("alt")
    if (path is None) or (alt is None) or (alt == PRIMARY_ALT):
        return Response("", status=HTTPStatus.UNPROCESSABLE_ENTITY)

    pad: Pad = g.admin_context.pad
    record: Record = pad.get(path, alt=alt)
    Path(record.source_filename).unlink()
    primary: Record = pad.get(path, alt=PRIMARY_ALT)
    node: TreeItem = g.admin_context.tree.get(path)
    return render_template("partials/content-translations.html",
                           record=primary, alts=node.alts)


def slug_from_title() -> Response:
    title = request.args.get("title")
    if title is None:
        return Response("", status=HTTPStatus.UNPROCESSABLE_ENTITY)

    slug = slugify(title)
    response = Response(slug)
    detail = '{"target": "%(sel)s", "attr": "%(att)s", "value": "%(val)s"}' % {
        "sel": "#field-_slug",
        "att": "value",
        "val": slug,
    }
    trigger = '{"updateAttr": %(detail)s}' % {"detail": detail}
    response.headers["HX-Trigger"] = trigger
    return response


def new_subpage() -> Response:
    endpoint = request.args.get("op")
    if endpoint is None:
        return Response("", status=HTTPStatus.UNPROCESSABLE_ENTITY)

    if endpoint == "add_translation":
        lang = request.args.get("lang")
        if lang is None:
            return Response("", status=HTTPStatus.UNPROCESSABLE_ENTITY)

    pad: Pad = g.admin_context.pad
    record, status = _record(pad, request.args, alt=PRIMARY_ALT)
    if record is None:
        return Response("", status=status)

    if endpoint == "add_subpage":
        child_models = utils.get_child_models(record)
        models = sorted(child_models, key=i18n_name)
        lang = None
    elif endpoint == "add_translation":
        models = [record.datamodel]
    markup = render_template("partials/new-subpage-dialog.html", record=record,
                             models=models, lang=lang, endpoint=endpoint)
    response = Response(markup)
    trigger = '{"showModal": {"modal": "#new-subpage-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def add_subpage() -> Response:
    model = request.form.get("model")
    if model is None:
        return Response("", status=HTTPStatus.UNPROCESSABLE_ENTITY)

    title = request.form.get("title", "").strip()
    if title == "":
        errors = [_("Every content item must have a title.")]
        return error_response(errors)

    pad: Pad = g.admin_context.pad
    parent, status = _record(pad, request.args, alt=PRIMARY_ALT)
    if parent is None:
        return Response("", status=status)

    try:
        path = utils.create_subpage(pad=pad, parent=parent.path, model=model,
                                    title=title, form=request.form)
    except FileExistsError:
        errors = [_("A content item with this name already exists.")]
        return error_response(errors)

    response = Response("")
    record_url = url_for("tekir_admin.edit_content", path=path)
    response.headers["HX-Redirect"] = record_url
    return response


def add_translation() -> Response:
    pad: Pad = g.admin_context.pad
    record, status = _record(pad, request.args, alt=PRIMARY_ALT)
    if record is None:
        return Response("", status=status)

    alt = request.args.get("lang")
    if (alt is None) or (alt == PRIMARY_ALT):
        return Response("", status=HTTPStatus.UNPROCESSABLE_ENTITY)

    try:
        utils.create_translation(pad=pad, record=record, alt=alt,
                                 form=request.form)
    except FileExistsError:
        errors = [_("A translation for this language already exists.")]
        return error_response(errors)

    response = Response("")
    record_url = url_for("tekir_admin.edit_content", path=record.path, alt=alt)
    response.headers["HX-Redirect"] = record_url
    return response


def upload_attachment() -> Response:
    endpoint = request.args.get("op")
    if endpoint is None:
        return Response("", status=HTTPStatus.UNPROCESSABLE_ENTITY)

    pad: Pad = g.admin_context.pad
    record, status = _record(pad, request.args, alt=PRIMARY_ALT)
    if record is None:
        return Response("", status=status)

    markup = render_template("partials/upload-dialog.html", record=record,
                             endpoint=endpoint)
    response = Response(markup)
    trigger = '{"showModal": {"modal": "#upload-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def add_attachment() -> Response:
    uploaded = request.files.get("file")
    if uploaded is None:
        errors = [_("Please upload a file.")]
        return error_response(errors)

    pad: Pad = g.admin_context.pad
    record, status = _record(pad, request.args, alt=PRIMARY_ALT)
    if record is None:
        return Response("", status=status)

    try:
        path = utils.create_attachment(pad=pad, parent=record,
                                       uploaded=uploaded)
    except FileExistsError:
        errors = [_("An attachment with this name already exists.")]
        return error_response(errors)

    response = Response()
    record_url = url_for("tekir_admin.contents", path=path, alt=PRIMARY_ALT)
    response.headers["HX-Redirect"] = record_url
    return response


def replace_attachment() -> Response:
    uploaded = request.files.get("file")
    if uploaded is None:
        errors = [_("Please upload a file.")]
        return error_response(errors)

    pad: Pad = g.admin_context.pad
    record, status = _record(pad, request.args, alt=PRIMARY_ALT)
    if record is None:
        return Response("", status=status)

    source_path = Path(pad.db.to_fs_path(record.path))
    uploaded.save(source_path)

    response = Response("")
    record_url = url_for("tekir_admin.contents", path=record.path,
                         alt=PRIMARY_ALT)
    response.headers["HX-Redirect"] = record_url
    return response


def save_content() -> Response:
    record, status = _record(g.admin_context.pad, request.args)
    if record is None:
        return Response("", status=status)
    source = utils.get_source(record, request.form)
    source_path = Path(record.source_filename)
    if source == source_path.read_text():
        message = _("No changes.")
    else:
        source_path.write_text(source)
        message = _("Content saved.")

    markup = render_template("partials/save-dialog.html", message=message,
                             record=record)
    response = Response(markup)
    trigger = '{"showModal": {"modal": "#save-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def check_changes() -> Response:
    record, status = _record(g.admin_context.pad, request.args)
    if record is None:
        return Response("", status=status)
    record_url = url_for("tekir_admin.contents", path=record.path,
                         alt=record.alt)
    source = utils.get_source(record, request.form)
    source_path = Path(record.source_filename)
    if source == source_path.read_text():
        response = Response("")
        response.headers["HX-Redirect"] = record_url
    else:
        message = _("There are unsaved changes. Do you want to continue?")
        markup = render_template("partials/changes-dialog.html",
                                 message=message, record_url=record_url)
        response = Response(markup)
        trigger = '{"showModal": {"modal": "#changes-dialog"}}'
        response.headers["HX-Trigger-After-Swap"] = trigger
        response.headers["HX-Trigger"] = trigger
    return response


def new_flowblock() -> str | Response:
    field_name = request.args.get("field_name")
    flow_type = request.args.get("flow_type")
    if (field_name is None) or (flow_type is None):
        return Response("", status=HTTPStatus.UNPROCESSABLE_ENTITY)

    record, status = _record(g.admin_context.pad, request.args)
    if record is None:
        return Response("", status=status)

    block = utils.create_flowblock(record=record, flow_type=flow_type)
    uuid_index = uuid4().hex
    return render_template("tekir_flowblock.html",
                           block=block,
                           field_name=field_name,
                           block_index=f"uuid_{uuid_index}")


def start_navigate() -> str | Response:
    field_id = request.args.get("field_id")
    if field_id is None:
        return Response("", status=HTTPStatus.UNPROCESSABLE_ENTITY)

    pad: Pad = g.admin_context.pad
    record, status = _record(pad, request.args)
    if status == HTTPStatus.NOT_FOUND:
        return Response("", status=status)
    if record is None:
        record = pad.root

    navigables = utils.get_navigables(record)
    markup = render_template("partials/navigate-dialog.html",
                             navigables=navigables, field_id=field_id)
    response = Response(markup)
    trigger = '{"showModal": {"modal": "#navigate-dialog"}}'
    response.headers["HX-Trigger-After-Swap"] = trigger
    return response


def navigables() -> str | Response:
    record, status = _record(g.admin_context.pad, request.args)
    if record is None:
        return Response("", status=status)
    navigables = utils.get_navigables(record)
    return render_template("partials/navigables.html", navigables=navigables)


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
    bp.add_url_rule("/content-translations", view_func=content_translations)
    bp.add_url_rule("/content-subpages", view_func=content_subpages)
    bp.add_url_rule("/content-attachments", view_func=content_attachments)

    bp.add_url_rule("/delete-confirm", view_func=delete_confirm,
                    methods=["POST"])
    bp.add_url_rule("/delete-translation-confirm",
                    view_func=delete_translation_confirm)
    bp.add_url_rule("/delete-content", view_func=delete_content,
                    methods=["POST"])
    bp.add_url_rule("/delete-translation", view_func=delete_translation)

    bp.add_url_rule("/slugify", view_func=slug_from_title)
    bp.add_url_rule("/new-subpage", view_func=new_subpage)
    bp.add_url_rule("/add-subpage", view_func=add_subpage,
                    methods=["POST"])
    bp.add_url_rule("/add-translation", view_func=add_translation,
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

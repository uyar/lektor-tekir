# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from flask import Blueprint, Response, g, render_template, request, url_for
from flask_babel import gettext as _
from lektor.db import Record
from lektor.publisher import publish
from lektor.types.flow import FlowBlock
from slugify import slugify

from . import utils


FILE_MANAGERS = {
    "darwin": "open",
    "linux": "xdg-open",
    "win32": "explorer",
}


def page_count():
    root_path = Path(g.admin_context.pad.root.source_filename).parent
    pages = {c.parent for c in root_path.glob("**/contents*.lr")}
    return str(len(pages))


def open_folder():
    fs_path = request.args.get("fs_path")
    if fs_path is None:
        path = request.args.get("path", "/")
        record = g.admin_context.tree.get(path)._primary_record
        fs_path = Path(record.source_filename).parent
    subprocess.run([FILE_MANAGERS[sys.platform], fs_path])
    return ""


def clean_build():
    builder = g.admin_context.info.get_builder()
    builder.prune(all=True)
    builder.touch_site_config()
    return _("No output")


def build():
    builder = g.admin_context.info.get_builder()
    builder.build_all()
    builder.touch_site_config()
    output_path = Path(builder.destination_path)
    home_page = output_path / "index.html"
    if home_page.exists():
        mtime = int(home_page.stat().st_mtime)
        output_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
    else:
        output_time = _("No output")
    return output_time


def publish_build():
    pad = g.admin_context.pad
    output_path = g.admin_context.info.get_builder().destination_path
    server_id = request.form.get("server")
    server_info = pad.config.get_server(server_id)
    event_iter = publish(pad.env, server_info.target, output_path,
                         server_info=server_info)
    for line in event_iter:
        print(line)
    return ""


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


def save_content():
    path = request.args.get("path")
    record = g.admin_context.tree.get(path)._primary_record
    content = utils.get_content(record, request.form)
    source = Path(record.source_filename)
    old_content = source.read_text()
    if content == old_content:
        return _("No changes.")
    else:
        source.write_text(content)
        return _("Content saved.")


def check_changes():
    path = request.args.get("path")
    record = g.admin_context.tree.get(path)._primary_record
    content = utils.get_content(record, request.form)
    source = Path(record.source_filename)
    record_url = url_for("tekir_admin.contents", path=record.path)
    old_content = source.read_text()
    if content == old_content:
        response = Response("")
        response.headers["HX-Redirect"] = record_url
    else:
        message = _("There are unsaved changes. Do you want to continue?")
        trigger = '{"showChanges": {"href": "%s"}}' % record_url
        response = Response(message)
        response.headers["HX-Trigger"] = trigger
    return response


def check_delete():
    items = request.form.getlist("selected-items")
    root_path = Path(g.admin_context.pad.root.source_filename).parent
    result = []
    for path in items:
        record = g.admin_context.tree.get(path)._primary_record
        if record.is_attachment:
            result.append(record.path[1:])
        else:
            item_dir = Path(record.source_filename).parent
            for item in item_dir.glob("**/*"):
                if item.is_file():
                    item_path = str(item.relative_to(root_path))
                    result.append(item_path)
    return "\n".join(f'<li>{p}</li>' for p in sorted(result))


def delete_content():
    items = request.form.getlist("selected-items")
    for path in items:
        record = g.admin_context.tree.get(path)._primary_record
        if record.is_attachment:
            filename = record.source_filename.rstrip(".lr")
            Path(filename).unlink()
        else:
            item_dir = Path(record.source_filename).parent
            rmtree(item_dir)
    return _("Deleted.")


def new_flowblock():
    flow_type = request.args.get("flow_type")
    field_name = request.args.get("field_name")
    path = request.args.get("path")
    record = g.admin_context.tree.get(path)._primary_record
    data = {"_flowblock": flow_type}
    block = FlowBlock(data=data, pad=record.pad, record=record)
    uuid_index = uuid4().hex
    return render_template("tekir_flowblock.html", block=block,
                           field_name=field_name,
                           block_index=f"uuid_{uuid_index}")


def slug_from_title():
    title = request.args.get("title")
    slug = slugify(title)
    response = Response(slug)
    response.headers["HX-Trigger"] = '{"updateSlug": {"slug": "%s"}}' % slug
    return response


def new_content():
    parent = request.args.get("parent")
    model = request.form.get("model")
    title = request.form.get("title").strip()
    if not title:
        return _("Every content item must have a title.")
    slug = request.form.get("slug") or slugify(title)
    path = f"{parent}/{slug}" if parent != "/" else f"/{slug}"
    existing = g.admin_context.tree.get(path)._primary_record
    if existing is not None:
        return _("A content item with this name already exists.")
    pad = g.admin_context.pad
    data = {
        "_model": model,
        "_template": pad.db.datamodels[model].get_default_template_name(),
        "_slug": slug,
        "_path": path,
        "_alt": pad.root.alt,
    }
    record = Record(data=data, pad=pad)
    source_path = Path(pad.db.to_fs_path(record.path))
    source_path.mkdir()
    contents_file = source_path / "contents.lr"
    contents_file.write_text(utils.get_content(record, request.form))
    response = Response("OK")
    record_url = url_for("tekir_admin.edit_content", path=path)
    response.headers["HX-Redirect"] = record_url
    return response


def new_attachment():
    uploaded = request.files.get("file")
    if not uploaded:
        return _("Add")
    parent = request.args.get("parent")
    slug = uploaded.filename
    path = f"{parent}/{slug}" if parent != "/" else f"/{slug}"
    pad = g.admin_context.pad
    record = g.admin_context.tree.get(parent)._primary_record
    source_path = Path(pad.db.to_fs_path(record.path))
    attachment_path = source_path / uploaded.filename
    if attachment_path.exists():
        return _("An attachment with this name already exists for this item.")
    uploaded.save(attachment_path)
    response = Response("OK")
    record_url = url_for("tekir_admin.edit_attachment", path=path)
    response.headers["HX-Redirect"] = record_url
    return response


def replace_attachment():
    uploaded = request.files.get("file")
    if not uploaded:
        return _("Upload")
    path = request.args.get("path")
    pad = g.admin_context.pad
    source_path = Path(pad.db.to_fs_path(path))
    uploaded.save(source_path)
    response = Response("OK")
    record_url = url_for("tekir_admin.edit_attachment", path=path)
    response.headers["HX-Redirect"] = record_url
    return response


def make_blueprint():
    bp = Blueprint("api", __name__, url_prefix="/api")

    bp.add_url_rule("/page-count", view_func=page_count)
    bp.add_url_rule("/open-folder", view_func=open_folder)
    bp.add_url_rule("/clean-build", view_func=clean_build)
    bp.add_url_rule("/build", view_func=build)
    bp.add_url_rule("/publish-build", view_func=publish_build,
                    methods=["POST"])
    bp.add_url_rule("/navigables", view_func=navigables)
    bp.add_url_rule("/save-content", view_func=save_content,
                    methods=["POST"])
    bp.add_url_rule("/check-changes", view_func=check_changes,
                    methods=["POST"])
    bp.add_url_rule("/check-delete", view_func=check_delete,
                    methods=["POST"])
    bp.add_url_rule("/delete-content", view_func=delete_content,
                    methods=["POST"])
    bp.add_url_rule("/new-flowblock", view_func=new_flowblock)
    bp.add_url_rule("/slugify", view_func=slug_from_title)
    bp.add_url_rule("/new-content", view_func=new_content,
                    methods=["POST"])
    bp.add_url_rule("/new-attachment", view_func=new_attachment,
                    methods=["POST"])
    bp.add_url_rule("/replace-attachment", view_func=replace_attachment,
                    methods=["POST"])

    return bp

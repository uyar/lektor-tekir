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


MULTILINE = {"text", "strings", "markdown", "html", "rst", "flow"}

FILE_MANAGERS = {
    "darwin": "open",
    "linux": "xdg-open",
    "win32": "explorer",
}

bp = Blueprint("tekir_admin_api", __name__, url_prefix="/tekir-admin/api")


@bp.route("/page-count")
def page_count():
    root_path = Path(g.admin_context.pad.root.source_filename).parent
    pages = {c.parent for c in root_path.glob("**/contents*.lr")}
    return str(len(pages))


@bp.route("/open-folder")
def open_folder():
    fs_path = request.args.get("fs_path")
    if fs_path is None:
        path = request.args.get("path")
        record = g.admin_context.tree.get(path)._primary_record
        fs_path = Path(record.source_filename).parent
    subprocess.run([FILE_MANAGERS[sys.platform], fs_path])
    return ""


@bp.route("/clean-build")
def clean_build():
    g.lang_code = request.args.get("lang", "en")
    builder = g.admin_context.info.get_builder()
    builder.prune(all=True)
    builder.touch_site_config()
    return _("No output")


@bp.route("/build")
def build():
    g.lang_code = request.args.get("lang", "en")
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


@bp.route("/publish", methods=["POST"])
def deploy():
    pad = g.admin_context.pad
    output_path = g.admin_context.info.get_builder().destination_path
    server_id = request.form.get("server")
    server_info = pad.config.get_server(server_id)
    event_iter = publish(pad.env, server_info.target, output_path,
                         server_info=server_info)
    for line in event_iter:
        print(line)
    return ""


@bp.route("/navigables")
def navigables():
    g.lang_code = request.args.get("lang", "en")
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


def field_entry(field, field_name=None):
    if field_name is None:
        field_name = field.name
    value = request.form.get(field_name)
    if field.type.name == "boolean":
        value = "yes" if value == "on" else "no"
        if field.default in {"true", "yes", "1"}:
            default = "yes"
        elif field.default in {"false", "no", "0"}:
            default = "no"
        if value == default:
            value = None
    if value is not None:
        value = value.strip()
    if not value:
        return None
    if field.type.name in MULTILINE:
        stripped = "\n".join(line.rstrip() for line in value.splitlines())
        return f"{field.name}:\n\n{stripped}"
    else:
        return f"{field.name}: {value}"


def flowblock_entry(record, field):
    block_data = [k for k in request.form if k.startswith(f"{field.name}-")]
    if len(block_data) == 0:
        return None
    block_indexes = []
    for i in [k.split("-")[1] for k in block_data]:
        if i not in block_indexes:
            block_indexes.append(i)
    entries = []
    for i in block_indexes:
        prefix = f"{field.name}-{i}-"
        block_fields = [k for k in request.form if k.startswith(prefix)]
        block_types = {f.split("-")[2] for f in block_fields}
        if len(block_types) > 1:
            raise RuntimeError("All fields must be of the same flowblock type")
        block_type_id = block_fields[0].split("-")[2]
        block_header = f"#### {block_type_id} ####"
        block_type = record.pad.db.flowblocks[block_type_id]
        block_entries = []
        for block_field in block_type.fields:
            field_name = f"{field.name}-{i}-{block_type_id}-{block_field.name}"
            block_entry = field_entry(block_field, field_name)
            if not block_entry:
                continue
            block_entries.append(block_entry)
        entries.append(block_header + "\n" + "\n----\n".join(block_entries))
    return f"{field.name}:\n\n" + "\n".join(entries)


def get_content(record):
    entries = []

    try:
        default_model = record.parent.datamodel.child_config.model
    except AttributeError:
        default_model = None
    if default_model is None:
        default_model = "page"
    if record["_model"] != default_model:
        entries.append(f"_model: {record['_model']}")

    if record["_template"] != record.datamodel.get_default_template_name():
        entries.append(f"_template: {record['_template']}")

    for field in record.datamodel.fields:
        if field.type.name == "flow":
            entry = flowblock_entry(record, field)
        else:
            entry = field_entry(field)
        if not entry:
            continue
        entries.append(entry)

    return "\n---\n".join(entries) + "\n"


@bp.route("/save-content", methods=["POST"])
def save_content():
    g.lang_code = request.args.get("lang", "en")
    path = request.args.get("path")
    record = g.admin_context.tree.get(path)._primary_record
    content = get_content(record)
    source = Path(record.source_filename)
    old_content = source.read_text()
    if content == old_content:
        return _("No changes.")
    else:
        source.write_text(content)
        return _("Content saved.")


@bp.route("/check-changes", methods=["POST"])
def check_changes():
    g.lang_code = request.args.get("lang", "en")
    path = request.args.get("path")
    record = g.admin_context.tree.get(path)._primary_record
    content = get_content(record)
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


@bp.route("/check-delete", methods=["POST"])
def check_delete():
    g.lang_code = request.args.get("lang", "en")
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


@bp.route("/delete-content", methods=["POST"])
def delete_content():
    g.lang_code = request.args.get("lang", "en")
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


@bp.route("/new-flowblock")
def new_flowblock():
    g.lang_code = request.args.get("lang", "en")
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


@bp.route("/slugify")
def slug_from_title():
    title = request.args.get("title")
    slug = slugify(title)
    response = Response(slug)
    response.headers["HX-Trigger"] = '{"updateSlug": {"slug": "%s"}}' % slug
    return response


@bp.route("/new-content", methods=["POST"])
def new_content():
    g.lang_code = request.args.get("lang", "en")
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
    contents_file.write_text(get_content(record))
    response = Response("OK")
    record_url = url_for("tekir_admin.edit_content", path=path)
    response.headers["HX-Redirect"] = record_url
    return response


@bp.route("/new-attachment", methods=["POST"])
def new_attachment():
    g.lang_code = request.args.get("lang", "en")
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

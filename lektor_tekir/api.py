# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from pathlib import Path
from shutil import rmtree

from flask import Blueprint, Response, g, render_template, request, url_for
from flask_babel import gettext as _
from lektor.types.flow import FlowBlock


MULTILINE = {"text", "strings", "markdown", "html", "rst", "flow"}


bp = Blueprint("tekir_admin_api", __name__, url_prefix="/tekir-admin/api")


@bp.route("/page-count")
def page_count():
    root_path = Path(g.admin_context.pad.root.source_filename).parent
    pages = {c.parent for c in root_path.glob("**/contents*.lr")}
    return str(len(pages))


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


def flowblock_entry(node, field):
    block_data = [k for k in request.form if k.startswith(f"{field.name}-")]
    if len(block_data) == 0:
        return None
    block_indexes = []
    for i in [int(k.split("-")[1]) for k in block_data]:
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
        block_type = node.tree.pad.db.flowblocks[block_type_id]
        block_entries = []
        for block_field in block_type.fields:
            field_name = f"{field.name}-{i}-{block_type_id}-{block_field.name}"
            block_entry = field_entry(block_field, field_name)
            if not block_entry:
                continue
            block_entries.append(block_entry)
        entries.append(block_header + "\n" + "\n----\n".join(block_entries))
    return f"{field.name}:\n\n" + "\n".join(entries)


def get_content(node):
    record = node._primary_record
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
            entry = flowblock_entry(node, field)
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
    node = g.admin_context.tree.get(path)
    content = get_content(node)
    source = Path(node._primary_record.source_filename)
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
    node = g.admin_context.tree.get(path)
    content = get_content(node)
    record = node._primary_record
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
    path = request.args.get("path")
    record = g.admin_context.tree.get(path)._primary_record
    block = FlowBlock(data={"_flowblock": flow_type}, pad=g.admin_context.pad,
                      record=record)
    return render_template("tekir_flowblock.html", record=record, block=block,
                           field_name="slides", block_index=666, open=True)

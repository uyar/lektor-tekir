# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

MULTILINE = {"text", "strings", "markdown", "html", "rst", "flow"}


def get_ancestors(record):
    ancestors = []
    current = record
    while current.parent:
        current = current.parent
        ancestors.append(current)
    ancestors.reverse()
    return ancestors


def field_entry(field, form, field_name=None):
    if field_name is None:
        field_name = field.name
    value = form.get(field_name)
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


def flowblock_entry(record, field, form):
    block_data = [k for k in form if k.startswith(f"{field.name}-")]
    if len(block_data) == 0:
        return None
    block_indexes = []
    for i in [k.split("-")[1] for k in block_data]:
        if i not in block_indexes:
            block_indexes.append(i)
    entries = []
    for i in block_indexes:
        prefix = f"{field.name}-{i}-"
        block_fields = [k for k in form if k.startswith(prefix)]
        block_types = {f.split("-")[2] for f in block_fields}
        if len(block_types) > 1:
            raise RuntimeError("All fields must be of the same flowblock type")
        block_type_id = block_fields[0].split("-")[2]
        block_header = f"#### {block_type_id} ####"
        block_type = record.pad.db.flowblocks[block_type_id]
        block_entries = []
        for block_field in block_type.fields:
            field_name = f"{field.name}-{i}-{block_type_id}-{block_field.name}"
            block_entry = field_entry(block_field, form, field_name)
            if not block_entry:
                continue
            block_entries.append(block_entry)
        entries.append(block_header + "\n" + "\n----\n".join(block_entries))
    return f"{field.name}:\n\n" + "\n".join(entries)


def get_content(record, form):
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
            entry = flowblock_entry(record, field, form)
        else:
            entry = field_entry(field, form)
        if not entry:
            continue
        entries.append(entry)

    return "\n---\n".join(entries) + "\n"

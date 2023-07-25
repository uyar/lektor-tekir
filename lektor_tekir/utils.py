# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from lektor.builder import Builder
from lektor.datamodel import DataModel, Field, FlowBlockModel
from lektor.db import Record
from werkzeug.datastructures.structures import ImmutableMultiDict


BOOL_VALUES: dict[str, str] = {"true": "yes", "false": "no",
                               "1": "yes", "0": "no"}
MULTILINE: set[str] = {"text", "strings", "markdown", "html", "rst", "flow"}

ENTRY_SEP = "---\n"
BLOCK_SEP = "----\n"


def get_page_count(record: Record) -> int:
    fs_path = Path(record.source_filename).parent
    pages: set[Path] = {c.parent for c in fs_path.glob("**/contents*.lr")}
    return len(pages)


def get_output_time(builder: Builder) -> datetime | None:
    output_path = Path(builder.destination_path)
    home_page = output_path / "index.html"
    if not home_page.exists():
        return None
    mtime = int(output_path.stat().st_mtime)
    return datetime.fromtimestamp(mtime)


def get_ancestors(record: Record) -> list[Record]:
    ancestors: list[Record] = []
    current = record
    while current.parent:
        current = current.parent
        ancestors.append(current)
    ancestors.reverse()
    return ancestors


def get_child_models(record: Record) -> list[DataModel]:
    data_models: dict[str, DataModel] = record.pad.db.datamodels
    allowed_model: str | None = record.datamodel.child_config.model
    if allowed_model is not None:
        return [data_models[allowed_model]]
    return [m for m in data_models.values() if not m.hidden]


def field_entry(field: Field, form: ImmutableMultiDict, *,
                form_field: str | None = None) -> str:
    field_name: str = form_field if form_field is not None else field.name
    value: str = form.get(field_name, "").strip()

    if field.type.name == "boolean":
        value = "yes" if value == "on" else "no"
        if value == BOOL_VALUES.get(field.default, field.default):
            value = ""

    if not value:
        return ""

    if field.type.name in MULTILINE:
        stripped = "\n".join(line.rstrip() for line in value.splitlines())
        return f"{field.name}:\n\n{stripped}\n"
    else:
        return f"{field.name}: {value}\n"


def flowblock_entry(record: Record, field: Field,
                    form: ImmutableMultiDict) -> str:
    all_block_fields: list[str] = [k for k in form
                                   if k.startswith(f"{field.name}-")]
    if len(all_block_fields) == 0:
        return ""

    block_ids: list[str] = []
    for i in [k.split("-")[1] for k in all_block_fields]:
        if i not in block_ids:
            block_ids.append(i)

    entries: list[str] = []
    for i in block_ids:
        prefix = f"{field.name}-{i}-"
        block_fields = [k for k in form if k.startswith(prefix)]

        block_model_ids: set[str] = {f.split("-")[2] for f in block_fields}
        if len(block_model_ids) > 1:
            raise RuntimeError("All fields must be of the same flowblock type")
        block_model_id: str = list(block_model_ids)[0]
        block_model: FlowBlockModel = record.pad.db.flowblocks[block_model_id]
        block_header = f"#### {block_model_id} ####\n"
        block_prefix = f"{field.name}-{i}-{block_model_id}-"

        block_entries: list[str] = []
        for block_field in block_model.fields:
            form_field = f"{block_prefix}{block_field.name}"
            block_entry: str = field_entry(block_field, form,
                                           form_field=form_field)
            if block_entry == "":
                continue
            block_entries.append(block_entry)
        entries.append(block_header + BLOCK_SEP.join(block_entries))
    return f"{field.name}:\n\n" + "".join(entries)


def get_content(record: Record, form: ImmutableMultiDict):
    entries: list[str] = []

    default_model: str = "page"
    try:
        allowed_model = record.parent.datamodel.child_config.model
        if allowed_model is not None:
            default_model = allowed_model
    except AttributeError:
        pass
    if record["_model"] != default_model:
        entries.append(f"_model: {record['_model']}\n")

    model: DataModel = record.datamodel
    if record["_template"] != model.get_default_template_name():
        entries.append(f"_template: {record['_template']}\n")

    fields: list[Field] = model.fields
    for field in fields:
        if field.type.name == "flow":
            entry = flowblock_entry(record, field, form)
        else:
            entry = field_entry(field, form)
        if entry == "":
            continue
        entries.append(entry)

    return ENTRY_SEP.join(entries)

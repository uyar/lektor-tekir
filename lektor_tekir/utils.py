# Copyright (C) 2023 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-tekir is released under the BSD license.
# Read the included LICENSE.txt file for details.

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from shutil import rmtree
from typing import Mapping
from uuid import uuid4

from lektor.builder import Builder
from lektor.constants import PRIMARY_ALT
from lektor.datamodel import DataModel, Field, FlowBlockModel
from lektor.db import Pad, Page, Record
from lektor.types.flow import FlowBlock
from slugify import slugify
from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.datastructures.structures import ImmutableMultiDict


BOOL_VALUES: dict[str, str] = {"true": "yes", "false": "no",
                               "1": "yes", "0": "no"}
MULTILINE: set[str] = {"text", "strings", "markdown", "html", "rst", "flow"}

ENTRY_SEP = "---\n"
BLOCK_SEP = "----\n"

SYSTEM_FIELDS: list[str] = ["_slug", "_template", "_hidden", "_discoverable"]


def get_page_count(record: Record) -> int:
    fs_path = Path(record.source_filename).parent
    pages = {c.parent for c in fs_path.glob("**/contents*.lr")}
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
        current = record.pad.get(current.parent.path, alt=current.alt)
        ancestors.append(current)
    ancestors.reverse()
    return ancestors


def get_record_paths(records: list[Record], *, root: Record) -> list[str]:
    root_fs_path = Path(root.source_filename).parent
    paths: list[str] = []
    for record in records:
        if record.is_attachment:
            paths.append(record.path[1:])  # strip the trailing '/'
        else:
            record_dir = Path(record.source_filename).parent
            for record_fs_path in record_dir.glob("**/*"):
                if record_fs_path.is_file():
                    record_path = record_fs_path.relative_to(root_fs_path)
                    paths.append(str(record_path))
    return paths


def get_child_models(record: Record) -> list[DataModel]:
    data_models: dict[str, DataModel] = record.pad.db.datamodels
    allowed_model: str | None = record.datamodel.child_config.model
    if allowed_model is not None:
        return [data_models[allowed_model]]
    return [m for m in data_models.values() if not m.hidden]


def get_navigables(record: Record) -> list[tuple[str, str, bool]]:
    options: list[tuple[str, str, bool]] = [
        ("", "----", False),
        ("/", "/", record.path == "/"),
    ]
    for ancestor in get_ancestors(record)[1:]:
        options.append((ancestor.path, ancestor["_slug"], False))
    if record.path != "/":
        options.append((record.path, record["_slug"], True))
    for child in record.children:
        options.append((child.path, child["_slug"], False))
    return options


def field_entry(record: Record, field: Field, form: Mapping[str, str], *,
                form_field: str | None = None,
                primary: Record | None = None) -> str:
    field_name: str = form_field if form_field is not None else field.name
    value: str = form.get(field_name, "").strip()

    if field.type.name == "boolean":
        default_value = "yes" if field.default == "yes" else "no"
        value = "yes" if value == "on" else "no"
        if value == default_value:
            value = ""

    if field.name == "_slug":
        canonical = record if primary is None else primary
        if value == canonical["_slug"]:
            value = ""

    if field.name == "_template":
        model: DataModel = record.datamodel
        if value == model.get_default_template_name():
            value = ""

    if value == "":
        return ""

    if field.type.name in MULTILINE:
        stripped = "\n".join(line.rstrip() for line in value.splitlines())
        return f"{field.name}:\n\n{stripped}\n"
    else:
        return f"{field.name}: {value}\n"


def flowblock_entry(record: Record, field: Field, form: Mapping[str, str], *,
                    primary: Record | None = None) -> str:
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
        block_model_id = list(block_model_ids)[0]
        block_model: FlowBlockModel = record.pad.db.flowblocks[block_model_id]
        block_header = f"#### {block_model_id} ####\n"
        block_prefix = f"{field.name}-{i}-{block_model_id}-"

        block_entries: list[str] = []
        for block_field in block_model.fields:
            form_field = f"{block_prefix}{block_field.name}"
            block_entry: str = field_entry(record, block_field, form,
                                           form_field=form_field,
                                           primary=primary)
            if block_entry == "":
                continue
            block_entries.append(block_entry)
        entries.append(block_header + BLOCK_SEP.join(block_entries))
    return f"{field.name}:\n\n" + "".join(entries)


def get_source(record: Record, form: Mapping[str, str], *,
               primary: Record | None = None) -> str:
    entries: list[str] = []
    model: DataModel = record.datamodel
    system_fields: list[Field] = [model.field_map[f] for f in SYSTEM_FIELDS]
    fields: list[Field] = system_fields + model.fields
    for field in fields:
        if field.type.name == "flow":
            entry = flowblock_entry(record, field, form, primary=primary)
        else:
            entry = field_entry(record, field, form, primary=primary)
        if entry == "":
            continue
        entries.append(entry)
    return ENTRY_SEP.join(entries)


def delete_record(record: Record) -> None:
    if record.is_attachment:
        filename: str = record.source_filename.rstrip(".lr")
        Path(filename).unlink()
    else:
        record_dir = Path(record.source_filename).parent
        rmtree(record_dir)


def create_subpage(*, pad: Pad, parent: str, model: str, title: str,
                   form: Mapping[str, str]) -> str:
    slug: str = form.get("_slug") or slugify(title)
    path = f"{parent}/{slug}" if parent != "/" else f"/{slug}"
    fs_path = Path(pad.db.to_fs_path(path))
    if fs_path.exists():
        raise FileExistsError("Duplicate slug")

    data: dict[str, str] = {
        "_model": model,
        "_template": pad.db.datamodels[model].get_default_template_name(),
        "_slug": slug,
        "_path": path,
        "_alt": PRIMARY_ALT,
    }
    page = Page(data=data, pad=pad)

    fs_path.mkdir()
    source_file = Path(page.source_filename)
    source = get_source(page, dict(**form, _discoverable="on"))
    source_file.write_text(source)
    return path


def create_translation(*, pad: Pad, record: Record, alt: str,
                       form: ImmutableMultiDict):
    model: str = record.datamodel.id
    slug: str = form.get("_slug") or record["_slug"]
    data: dict[str, str] = {
        "_model": model,
        "_template": pad.db.datamodels[model].get_default_template_name(),
        "_slug": slug,
        "_path": record.path,
        "_alt": alt,
    }
    page = Page(data=data, pad=pad)
    source_file = Path(page.source_filename)
    primary: Record = pad.get(record.path, alt=PRIMARY_ALT)
    source = get_source(page, dict(**form, _discoverable="on"),
                        primary=primary)
    source_file.write_text(source)


def create_attachment(*, pad: Pad, parent: Record,
                      uploaded: FileStorage) -> str:
    slug = uploaded.filename
    if slug is None:
        slug = uuid4().hex
    path = f"{parent.path}/{slug}" if parent.path != "/" else f"/{slug}"
    fs_path = Path(pad.db.to_fs_path(path))
    if fs_path.exists():
        raise FileExistsError("Duplicate slug")
    uploaded.save(fs_path)
    return path


def create_flowblock(*, record: Record, flow_type: str) -> FlowBlock:
    data: dict[str, str] = {"_flowblock": flow_type}
    return FlowBlock(data=data, pad=record.pad, record=record)

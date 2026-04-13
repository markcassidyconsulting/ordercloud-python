"""Renderer — generates Python source files from enriched IR via Jinja2."""

from __future__ import annotations

import keyword
import subprocess
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .ir import ModelGroup, OperationDef, ResourceDef

__all__ = ["render"]

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _safe_enum_name(value: str) -> str:
    """Make an enum member name safe for Python (prefix with _ if keyword)."""
    if keyword.iskeyword(value):
        return f"_{value}"
    return value


def _quote_path(path: str) -> str:
    """Quote a path template, using f-string only if it has interpolation."""
    if "{" in path:
        return f'f"{path}"'
    return f'"{path}"'


def _return_annotation(op: OperationDef) -> str:
    """Compute the return type annotation for an operation."""
    if op.return_is_list and op.return_type:
        return f"ListPage[{op.return_type}]"
    if op.return_type:
        return op.return_type
    return "None"


def _return_description(op: OperationDef) -> str:
    """Compute the Returns docstring line for an operation."""
    if op.return_is_list and op.return_type:
        return f"A paginated list of {op.return_type} objects."
    if op.return_type:
        return f"The {op.return_type} object."
    return ""


def _create_jinja_env() -> Environment:
    """Create a Jinja2 environment with the codegen templates."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        keep_trailing_newline=True,
        lstrip_blocks=True,
        trim_blocks=True,
    )
    # Register helper functions as globals so templates can call them.
    env.globals["_return_annotation"] = _return_annotation
    env.globals["_return_description"] = _return_description
    # Register filters.
    env.filters["safe_enum_name"] = _safe_enum_name
    env.filters["quote_path"] = _quote_path
    return env


def render(
    model_groups: list[ModelGroup],
    resources: list[ResourceDef],
    output_dir: Path,
    *,
    dry_run: bool = False,
    format_output: bool = True,
) -> list[Path]:
    """Render all generated files.

    Args:
        model_groups: Enriched model groups from the transformer.
        resources: Enriched resource definitions from the transformer.
        output_dir: Root of ``src/ordercloud/``.
        dry_run: If True, return file paths without writing.
        format_output: If True, run ``ruff format`` on each output file.

    Returns:
        List of paths that were (or would be) written.
    """
    env = _create_jinja_env()
    written: list[Path] = []

    models_dir = output_dir / "models"
    resources_dir = output_dir / "resources"

    # Ensure directories exist.
    if not dry_run:
        models_dir.mkdir(parents=True, exist_ok=True)
        resources_dir.mkdir(parents=True, exist_ok=True)

    # --- Model modules ---
    model_tmpl = env.get_template("model_module.py.j2")
    for group in model_groups:
        path = models_dir / f"{group.module_name}.py"
        content = model_tmpl.render(
            module_docstring=group.module_docstring,
            imports=group.imports,
            all_names=group.all_names,
            type_aliases=group.type_aliases,
            type_aliases_bottom=group.type_aliases_bottom,
            enums=group.enums,
            models=group.models,
        )
        written.append(path)
        if not dry_run:
            path.write_text(content, encoding="utf-8")

    # --- Models __init__.py ---
    # Deduplicate names across groups (re-exports can cause overlap).
    seen_names: set[str] = set()
    init_groups = []
    for group in model_groups:
        unique_names = [n for n in group.all_names if n not in seen_names]
        seen_names.update(unique_names)
        if unique_names:
            init_groups.append(ModelGroup(
                module_name=group.module_name,
                module_docstring=group.module_docstring,
                models=group.models,
                enums=group.enums,
                imports=group.imports,
                all_names=unique_names,
            ))
    models_init_tmpl = env.get_template("models_init.py.j2")
    path = models_dir / "__init__.py"
    content = models_init_tmpl.render(groups=init_groups)
    written.append(path)
    if not dry_run:
        path.write_text(content, encoding="utf-8")

    # --- Resource modules ---
    resource_tmpl = env.get_template("resource_module.py.j2")
    for resource in resources:
        path = resources_dir / f"{resource.module_name}.py"
        content = resource_tmpl.render(
            module_docstring=resource.module_docstring,
            import_lines=resource.import_lines,
            class_name=resource.class_name,
            class_docstring=resource.class_docstring,
            operations=resource.operations,
        )
        written.append(path)
        if not dry_run:
            path.write_text(content, encoding="utf-8")

    # --- Resources __init__.py ---
    resources_init_tmpl = env.get_template("resources_init.py.j2")
    path = resources_dir / "__init__.py"
    content = resources_init_tmpl.render(resources=resources)
    written.append(path)
    if not dry_run:
        path.write_text(content, encoding="utf-8")

    # --- Client ---
    client_tmpl = env.get_template("client.py.j2")
    path = output_dir / "client.py"
    content = client_tmpl.render(resources=resources)
    written.append(path)
    if not dry_run:
        path.write_text(content, encoding="utf-8")

    # --- Format output ---
    if format_output and not dry_run:
        _format_files(written)

    return written


def _format_files(paths: list[Path]) -> None:
    """Run ruff format on all generated files."""
    str_paths = [str(p) for p in paths if p.exists()]
    if not str_paths:
        return
    try:
        subprocess.run(
            ["ruff", "format", *str_paths],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        # ruff not available — skip formatting.
        pass
    except subprocess.CalledProcessError as e:
        print(f"Warning: ruff format failed: {e.stderr}")

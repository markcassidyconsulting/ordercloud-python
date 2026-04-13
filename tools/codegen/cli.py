"""CLI for the OrderCloud Python SDK code generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .grouping import validate_completeness
from .parser import parse_spec
from .renderer import render
from .transformer import transform

__all__ = ["main"]


def main(argv: list[str] | None = None) -> int:
    """Entry point for the codegen CLI."""
    parser = argparse.ArgumentParser(
        prog="ordercloud-codegen",
        description="Generate OrderCloud Python SDK models and resources from an OpenAPI spec.",
    )
    parser.add_argument(
        "--spec",
        type=Path,
        required=True,
        help="Path to the OrderCloud OpenAPI v3 JSON spec.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("src/ordercloud"),
        help="Output directory (default: src/ordercloud).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print file paths without writing.",
    )
    parser.add_argument(
        "--models-only",
        action="store_true",
        help="Generate only model files.",
    )
    parser.add_argument(
        "--resources-only",
        action="store_true",
        help="Generate only resource files.",
    )
    parser.add_argument(
        "--no-format",
        action="store_true",
        help="Skip ruff format on output.",
    )

    args = parser.parse_args(argv)

    if not args.spec.exists():
        print(f"Error: spec file not found: {args.spec}", file=sys.stderr)
        return 1

    # Parse.
    print(f"Parsing {args.spec}...")
    models, enums, resources, all_schemas = parse_spec(args.spec)
    print(f"  {len(models)} models, {len(enums)} enums, {len(resources)} resources")

    # Validate completeness.
    errors = validate_completeness(all_schemas)
    if errors:
        for e in errors:
            print(f"Error: {e}", file=sys.stderr)
        return 1
    print("  Schema completeness: OK")

    # Transform.
    print("Transforming...")
    model_groups, enriched_resources = transform(models, enums, resources)
    print(f"  {len(model_groups)} model groups, {len(enriched_resources)} resources")

    # Filter if requested.
    if args.models_only:
        enriched_resources = []
    if args.resources_only:
        model_groups = []

    # Render.
    print(f"{'Would write' if args.dry_run else 'Writing'} to {args.output}/...")
    written = render(
        model_groups,
        enriched_resources,
        args.output,
        dry_run=args.dry_run,
        format_output=not args.no_format,
    )

    for p in written:
        print(f"  {'[dry-run] ' if args.dry_run else ''}{p}")

    print(f"\n{'Would generate' if args.dry_run else 'Generated'} {len(written)} files.")
    return 0

"""svox CLI — batch voxel pipeline MVP."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from svox import __version__
from svox.export import export_all
from svox.generate import generate
from svox.normalize import load_manifest, normalize_job
from svox.stylize import stylize
from svox.validate import validate


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="svox", description="Stonehearth-flavored voxel batch pipeline (MVP)")
    p.add_argument("--version", action="version", version=f"svox {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="normalize → generate → stylize → export → validate")
    run.add_argument("--manifest", "-m", type=str, help="YAML job manifest")
    run.add_argument("--text", type=str, help="free-text description (optional)")
    run.add_argument("--theme", type=str, help="carrot|crate|stew|basket")
    run.add_argument("--size", type=str, help="W,H,D e.g. 12,20,12")
    run.add_argument("--seed", type=int, help="RNG seed")
    run.add_argument("--formats", type=str, default=None, help="comma list: vox,qb,glb")
    run.add_argument("--out", "-o", type=str, required=True, help="output directory")
    run.add_argument("--id", type=str, help="job id / output stem")
    run.add_argument("--backend", type=str, default=None)
    run.add_argument("--skip-validate", action="store_true")
    run.add_argument("--json", action="store_true", help="print machine-readable result")

    sub.add_parser("themes", help="list built-in procedural themes")
    return p


def cmd_themes() -> int:
    from svox.generate import GENERATORS
    from svox.normalize import THEME_DEFAULTS

    for name in sorted(GENERATORS):
        d = THEME_DEFAULTS.get(name, {})
        print(f"{name:10s} category={d.get('category','?')} size={d.get('size')}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest) if args.manifest else None
    formats = [f.strip() for f in args.formats.split(",")] if args.formats else None
    size = args.size
    job = normalize_job(
        manifest=manifest,
        text=args.text,
        theme=args.theme,
        size=size,
        seed=args.seed,
        formats=formats,
        backend=args.backend,
        job_id=args.id,
    )

    vol = generate(job)
    vol = stylize(vol, job)
    written = export_all(vol, job, args.out)
    report = validate(vol, job, written)

    result = {
        "job": job.to_dict(),
        "filled": vol.count_filled(),
        "size": list(vol.size),
        "outputs": {k: str(v) for k, v in written.items()},
        "validate": {"ok": report.ok, "errors": report.errors, "warnings": report.warnings},
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"job={job.id} theme={job.params.theme} seed={job.seed} filled={vol.count_filled()} size={vol.size}")
        for k, v in written.items():
            print(f"  {k}: {v} ({v.stat().st_size} bytes)")
        for w in report.warnings:
            print(f"  warning: {w}")
        if not report.ok:
            for e in report.errors:
                print(f"  error: {e}", file=sys.stderr)

    if not args.skip_validate and not report.ok:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "themes":
        return cmd_themes()
    if args.cmd == "run":
        return cmd_run(args)
    parser.error(f"unknown command {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
ChronoHash - File hashing, verification and comparison.
Part of the CHRONO SUITE.

For legal, defensive and educational use on systems you own or are
authorized to test.
"""

import argparse
import hashlib
import hmac
import json
import sys
import time
from pathlib import Path

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

VERSION = "1.0.0"
CHUNK_SIZE = 1024 * 1024  # 1 MiB
ALGOS = ["md5", "sha1", "sha256", "sha512", "sha3_256", "blake2b"]
DEFAULT_ALGO = "sha256"
LENGTH_TO_ALGO = {32: "md5", 40: "sha1", 64: "sha256", 128: "sha512"}

DISCLAIMER = "For legal, defensive and educational use on systems you own or are authorized to test."

console = Console()
err_console = Console(stderr=True)

CHRONO_ART = [
    " ██████╗██╗  ██╗██████╗  ██████╗ ███╗   ██╗ ██████╗ ",
    "██╔════╝██║  ██║██╔══██╗██╔═══██╗████╗  ██║██╔═══██╗",
    "██║     ███████║██████╔╝██║   ██║██╔██╗ ██║██║   ██║",
    "██║     ██╔══██║██╔══██╗██║   ██║██║╚██╗██║██║   ██║",
    "╚██████╗██║  ██║██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝",
    " ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ",
]
HASH_ART = [
    "██╗  ██╗ █████╗ ███████╗██╗  ██╗",
    "██║  ██║██╔══██╗██╔════╝██║  ██║",
    "███████║███████║███████╗███████║",
    "██╔══██║██╔══██║╚════██║██╔══██║",
    "██║  ██║██║  ██║███████║██║  ██║",
    "╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝",
]
GRADIENT = ["#00f5ff", "#00d4ff", "#00a8ff", "#7a6bff", "#b44dff", "#ff4dd2"]


def show_banner():
    text = Text(justify="center")
    if console.width >= 62:
        lines = CHRONO_ART + HASH_ART
        for i, line in enumerate(lines):
            color = GRADIENT[min(i * len(GRADIENT) // len(lines), len(GRADIENT) - 1)]
            text.append(line + "\n", style=f"bold {color}")
    else:
        text.append("C H R O N O H A S H\n", style="bold #00f5ff")
    text.append(f"\nfile integrity toolkit  //  CHRONO SUITE  v{VERSION}\n", style="bold white")
    text.append(DISCLAIMER, style="dim")
    console.print(Panel(Align.center(text), box=box.DOUBLE,
                        border_style="#00f5ff", padding=(1, 2)))



# ---------------------------------------------------------------- core ----

def hash_file(path, algos):
    """Hash a file in chunks with one or more algorithms (single read pass)."""
    hashers = {a: hashlib.new(a) for a in algos}
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(CHUNK_SIZE)
            if not chunk:
                break
            for h in hashers.values():
                h.update(chunk)
    return {a: h.hexdigest() for a, h in hashers.items()}


def collect_files(paths, recursive):
    """Expand input paths into a sorted list of files."""
    files = []
    for p in paths:
        path = Path(p)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            if not recursive:
                err_console.print(f"[yellow]Skipping directory (use -r):[/] {path}")
                continue
            files.extend(f for f in sorted(path.rglob("*")) if f.is_file())
        else:
            err_console.print(f"[red]Not found:[/] {path}")
    return files


def hash_many(files, algos, quiet=False):
    """Hash many files, returning {path: {algo: digest}} and a list of errors."""
    results, errors = {}, []
    with Progress(
        SpinnerColumn(), TextColumn("[cyan]{task.description}"),
        console=err_console, transient=True, disable=quiet or len(files) < 2,
    ) as progress:
        task = progress.add_task("hashing", total=None)
        for f in files:
            progress.update(task, description=f"hashing {f.name}")
            try:
                results[f] = hash_file(f, algos)
            except OSError as exc:
                errors.append((f, str(exc)))
    return results, errors


def hashes_equal(a, b):
    """Constant-time, case-insensitive digest comparison."""
    return hmac.compare_digest(a.strip().lower().encode(), b.strip().lower().encode())


def parse_checkfile(path):
    """Parse sha256sum-style lines: '<hash>  <filename>' (optional '*' binary marker)."""
    entries = []
    base = Path(path).parent
    for lineno, line in enumerate(Path(path).read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            err_console.print(f"[yellow]Line {lineno} malformed, skipped[/]")
            continue
        digest, name = parts[0], parts[1].lstrip("*")
        entries.append((digest, base / name))
    return entries


# ------------------------------------------------------------ commands ----

def cmd_hash(args):
    algos = args.algo or [DEFAULT_ALGO]
    files = collect_files(args.paths, args.recursive)
    if not files:
        err_console.print("[red]No files to hash.[/]")
        return 2

    start = time.perf_counter()
    results, errors = hash_many(files, algos, args.quiet)
    elapsed = time.perf_counter() - start

    if args.json:
        out = {str(p): d for p, d in results.items()}
        print(json.dumps(out, indent=2))
    elif args.plain:
        for p, d in results.items():
            print(f"{d[algos[0]]}  {p}")
    else:
        table = Table(title="ChronoHash Results", header_style="bold cyan")
        table.add_column("File", overflow="fold")
        for a in algos:
            table.add_column(a.upper(), overflow="fold")
        for p, d in results.items():
            table.add_row(str(p), *[d[a] for a in algos])
        console.print(table)
        console.print(f"[dim]{len(results)} file(s) in {elapsed:.2f}s[/]")

    if args.output:
        with open(args.output, "w") as fh:
            for p, d in results.items():
                fh.write(f"{d[algos[0]]}  {p}\n")
        err_console.print(f"[green]Checksums ({algos[0]}) written to {args.output}[/]")

    for f, msg in errors:
        err_console.print(f"[red]Error:[/] {f}: {msg}")
    return 1 if errors else 0


def cmd_verify(args):
    if args.checkfile:
        try:
            checks = parse_checkfile(args.checkfile)
        except OSError as exc:
            err_console.print(f"[red]Cannot read checkfile:[/] {exc}")
            return 2
    elif args.file and args.expected:
        checks = [(args.expected, Path(args.file))]
    else:
        err_console.print("[red]Provide FILE EXPECTED_HASH, or use -c CHECKFILE.[/]")
        return 2

    table = Table(title="ChronoHash Verify", header_style="bold cyan")
    table.add_column("File", overflow="fold")
    table.add_column("Algo")
    table.add_column("Status")
    failures = 0

    for expected, path in checks:
        algo = args.algo or LENGTH_TO_ALGO.get(len(expected.strip()))
        if not algo:
            table.add_row(str(path), "?", "[yellow]UNKNOWN HASH LENGTH[/]")
            failures += 1
            continue
        try:
            actual = hash_file(path, [algo])[algo]
        except OSError as exc:
            table.add_row(str(path), algo, f"[red]ERROR: {exc.strerror}[/]")
            failures += 1
            continue
        if hashes_equal(actual, expected):
            table.add_row(str(path), algo, "[green]OK[/]")
        else:
            table.add_row(str(path), algo, "[red]MISMATCH[/]")
            failures += 1

    console.print(table)
    if failures:
        console.print(Panel(f"[red]{failures} check(s) failed. Do NOT trust these files.[/]"))
        return 1
    console.print(Panel("[green]All checks passed.[/]"))
    return 0


def _dir_map(root, algo):
    root = Path(root)
    files = [f for f in sorted(root.rglob("*")) if f.is_file()]
    results, _ = hash_many(files, [algo], quiet=False)
    return {str(p.relative_to(root)): d[algo] for p, d in results.items()}


def cmd_compare(args):
    a, b = Path(args.a), Path(args.b)
    algo = args.algo or DEFAULT_ALGO

    if a.is_file() and b.is_file():
        try:
            ha, hb = hash_file(a, [algo])[algo], hash_file(b, [algo])[algo]
        except OSError as exc:
            err_console.print(f"[red]Error:[/] {exc}")
            return 2
        same = hashes_equal(ha, hb)
        console.print(f"[cyan]{a}[/]\n  {ha}\n[cyan]{b}[/]\n  {hb}")
        console.print(Panel("[green]IDENTICAL[/]" if same else "[red]DIFFERENT[/]"))
        return 0 if same else 1

    if a.is_dir() and b.is_dir():
        ma, mb = _dir_map(a, algo), _dir_map(b, algo)
        only_a = sorted(set(ma) - set(mb))
        only_b = sorted(set(mb) - set(ma))
        changed = sorted(k for k in set(ma) & set(mb) if not hashes_equal(ma[k], mb[k]))
        same_count = len(set(ma) & set(mb)) - len(changed)

        table = Table(title=f"Directory Diff ({algo})", header_style="bold cyan")
        table.add_column("Status")
        table.add_column("Path", overflow="fold")
        for k in changed:
            table.add_row("[yellow]CHANGED[/]", k)
        for k in only_a:
            table.add_row("[red]ONLY IN A[/]", k)
        for k in only_b:
            table.add_row("[blue]ONLY IN B[/]", k)
        if table.row_count:
            console.print(table)
        console.print(
            f"[green]{same_count} identical[/], [yellow]{len(changed)} changed[/], "
            f"[red]{len(only_a)} only in A[/], [blue]{len(only_b)} only in B[/]"
        )
        return 0 if not (changed or only_a or only_b) else 1

    err_console.print("[red]Both arguments must be files, or both must be directories.[/]")
    return 2


# ----------------------------------------------------------------- CLI ----

def build_parser():
    parser = argparse.ArgumentParser(
        prog="chronohash",
        description="ChronoHash - hash, verify and compare files. Part of the CHRONO SUITE.",
        epilog=DISCLAIMER,
    )
    parser.add_argument("-V", "--version", action="version", version=f"ChronoHash {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("hash", help="compute file hashes")
    p.add_argument("paths", nargs="+", help="files or directories")
    p.add_argument("-a", "--algo", action="append", choices=ALGOS,
                   help=f"algorithm (repeatable, default {DEFAULT_ALGO})")
    p.add_argument("-r", "--recursive", action="store_true", help="recurse into directories")
    p.add_argument("-o", "--output", metavar="FILE", help="write sha256sum-style checksum file")
    fmt = p.add_mutually_exclusive_group()
    fmt.add_argument("--json", action="store_true", help="JSON output")
    fmt.add_argument("--plain", action="store_true", help="plain 'hash  file' output")
    p.add_argument("-q", "--quiet", action="store_true", help="no progress spinner")
    p.set_defaults(func=cmd_hash)

    p = sub.add_parser("verify", help="verify a file against a hash or checksum file")
    p.add_argument("file", nargs="?", help="file to check")
    p.add_argument("expected", nargs="?", help="expected hash")
    p.add_argument("-c", "--checkfile", metavar="FILE", help="checksum file to verify")
    p.add_argument("-a", "--algo", choices=ALGOS, help="algorithm (default: detect from length)")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("compare", help="compare two files or two directories")
    p.add_argument("a", help="first file/directory")
    p.add_argument("b", help="second file/directory")
    p.add_argument("-a", "--algo", choices=ALGOS, help=f"algorithm (default {DEFAULT_ALGO})")
    p.set_defaults(func=cmd_compare)

    return parser


def main():
    parser = build_parser()
    if len(sys.argv) == 1:
        show_banner()
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args()
    try:
        sys.exit(args.func(args))
    except KeyboardInterrupt:
        err_console.print("\n[yellow]Interrupted.[/]")
        sys.exit(130)


if __name__ == "__main__":
    main()

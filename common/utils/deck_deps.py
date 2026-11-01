#!/usr/bin/env python3
"""A deck's own Python packages: `requirements.txt` beside its Makefile, pinned, installed once by
`make deps` (docs/container.md "From your deck's Makefile").

    deck_deps.py dir ROOT REQ       print the folder the file's packages install into (nothing else)
    deck_deps.py install ROOT REQ   install them there, once; print the folder

The folder is `ROOT/deps-<engine version>-py<X.Y>-<os>-<arch>-<sha256 of the file, 8 hex>`, so a
release, a Python, a platform or an edit to the file keys a folder of its own, and the Python
that runs this (the image's under a container runtime, the env's natively) is the one the
packages are built for; Make.common reads `dir` at every parse and puts `<folder>/site-packages`
on PYTHONPATH, the kernel's too. `install` makes a venv on this Python's own site-packages
(`--system-site-packages`), so pip counts what the env already carries as installed and fetches
only what it lacks (never a second numpy over the env's compiled stack, as `pip --target` would),
into a `.part-*` directory renamed to the folder last, with the `site-packages` link at its top as
the mark that it is whole: a half install leaves only a `.part-*`, swept by the next run. Every
line must be pinned (`==`, a direct reference, `--hash`, a wheel or archive by path or URL; `-r`,
`-c` and `-e` are refused): the key hashes the file, so an unpinned line would give two days two
folders of one name. A `.pth` file in the venv is warned of: PYTHONPATH does not read those.
"""

import argparse
import hashlib
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "_extensions" / "engine"))
import livery as livery_mod  # noqa: E402  (the engine's reader: its version)

REFUSED = ("-r", "--requirement", "-c", "--constraint", "-e", "--editable")
ARCHIVE = re.compile(r"\.(whl|zip|tar\.gz|tgz|tar\.bz2)$")


def key(req: Path) -> str:
    digest = hashlib.sha256(req.read_bytes()).hexdigest()[:8]
    return (f"deps-{livery_mod.engine_version()}-py{sys.version_info[0]}.{sys.version_info[1]}"
            f"-{sys.platform}-{platform.machine()}-{digest}")


def folder(root: Path, req: Path) -> Path:
    return root / key(req)


def unpinned(text: str) -> list[str]:
    """The lines that do not pin: a `-r`/`-c`/`-e` line, or a requirement with no `==`, direct
    reference, `--hash` or archive. Option lines (`--index-url`, `--find-links`, ...) pass."""
    bad = []
    for raw in text.splitlines():
        line = re.sub(r"(^|\s)#.*$", "", raw).strip()
        if not line:
            continue
        if line.startswith(REFUSED):
            bad.append(raw.strip())
        elif line.startswith("-"):
            continue   # an option line
        elif "==" in line or " @ " in line or "--hash=" in line or ARCHIVE.search(line.split()[0]):
            continue
        else:
            bad.append(raw.strip())
    return bad


def install(root: Path, req: Path) -> Path:
    bad = unpinned(req.read_text())
    if bad:
        print(f"{req}: every line must be pinned (==, @ <url>, --hash, a wheel or archive); -r, -c and -e are "
              "refused. Not pinned:\n  " + "\n  ".join(bad), file=sys.stderr)
        sys.exit(2)
    final = folder(root, req)
    if (final / "site-packages").exists():
        print(f"{final}: already installed")
        return final
    root.mkdir(parents=True, exist_ok=True)
    for stale in root.glob(final.name + ".part-*"):
        shutil.rmtree(stale, ignore_errors=True)
    part = Path(tempfile.mkdtemp(prefix=final.name + ".part-", dir=root))
    try:
        subprocess.run([sys.executable, "-m", "venv", "--system-site-packages", "--without-pip", str(part)], check=True)
        py = part / "bin" / "python"
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}   # make's export: never a requirement's answer
        subprocess.run([str(py), "-m", "pip", "install", "--disable-pip-version-check", "--no-input",
                        "--no-warn-script-location", "-r", str(req)], check=True, env=env, cwd=req.parent)
        purelib = Path(subprocess.run([str(py), "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
                                      check=True, capture_output=True, text=True, env=env).stdout.strip())
        pth = sorted(p.name for p in purelib.glob("*.pth"))
        if pth:
            print(f"warning: {req}: {', '.join(pth)} installed a .pth file, which PYTHONPATH does not read: a package "
                  "that needs one belongs in conda-env.yaml", file=sys.stderr)
        (part / "site-packages").symlink_to(purelib.relative_to(part))
        if final.exists():   # another make got there first (two decks on one file): theirs is whole
            shutil.rmtree(part, ignore_errors=True)
        else:
            os.rename(part, final)
    except BaseException:
        shutil.rmtree(part, ignore_errors=True)
        raise
    print(f"{final}: installed {req}")
    return final


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("dir", "install"):
        p = sub.add_parser(name)
        p.add_argument("root", type=Path)
        p.add_argument("req", type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "dir":
        print(folder(a.root, a.req))
    else:
        install(a.root, a.req)


if __name__ == "__main__":
    main()

# ChronoHash

> File hashing, verification and comparison. Part of the **CHRONO SUITE**.

ChronoHash is a single-file Python CLI for computing checksums, verifying downloads against published hashes, and diffing files or whole directories. It is built for Termux (no root required) and runs anywhere Python 3.8+ does.

## Features

- Multiple algorithms in one read pass: `md5`, `sha1`, `sha256`, `sha512`, `sha3_256`, `blake2b`
- Chunked reading, so large files never load fully into memory
- `verify` against a single hash or a `sha256sum`-style checksum file (algorithm auto-detected by hash length)
- `compare` two files or two directories (changed / only in A / only in B)
- Constant-time hash comparison
- Table, JSON or plain output
- Scriptable exit codes
- Styled startup banner that adapts to narrow phone screens

## Requirements

- Python 3.8+
- [`rich`](https://github.com/Textualize/rich)

## Setup (Termux)

**1. Install Python and git**

~~~bash
pkg update -y && pkg install -y python git
~~~

**2. Get the project**

~~~bash
git clone https://github.com/<your-username>/chronohash.git
cd chronohash
~~~

Or, if you created the files manually:

~~~bash
cd ~/chronohash
~~~

**3. Install dependencies**

~~~bash
pip install -r requirements.txt
~~~

**4. Test it**

~~~bash
python chronohash.py -h
~~~

### Access phone storage (optional)

To hash files in Downloads, DCIM and so on, run this once and allow the permission:

~~~bash
termux-setup-storage
~~~

Your files are then available at `~/storage/downloads`, `~/storage/shared`, `~/storage/dcim`, etc.

### Shortcut (optional)

Add an alias so you can type `chronohash` from any folder:

~~~bash
echo "alias chronohash='python ~/chronohash/chronohash.py'" >> ~/.bashrc
source ~/.bashrc
~~~

The examples below use `python chronohash.py`. If you set the alias, replace that with `chronohash`.

## Usage

~~~
python chronohash.py <command> [options]
~~~

Running with no arguments shows the banner and help.

| Command   | Purpose                                         |
|-----------|-------------------------------------------------|
| `hash`    | Compute hashes for files or folders             |
| `verify`  | Check a file against a hash or a checksum file  |
| `compare` | Compare two files or two folders                |

Global options: `-h` / `--help`, `-V` / `--version`.

### hash

~~~
python chronohash.py hash PATH [PATH ...] [options]
~~~

| Option                | Description                                           |
|-----------------------|-------------------------------------------------------|
| `-a`, `--algo ALGO`   | Algorithm. Repeatable. Default `sha256`               |
| `-r`, `--recursive`   | Recurse into folders                                  |
| `-o`, `--output FILE` | Write a `sha256sum`-style checksum file               |
| `--json`              | JSON output                                           |
| `--plain`             | Plain `hash  filename` output                         |
| `-q`, `--quiet`       | Hide the progress spinner                             |

Examples:

~~~bash
# Single file, default sha256
python chronohash.py hash file.iso

# Several algorithms at once
python chronohash.py hash file.iso -a md5 -a sha256 -a blake2b

# Whole folder, recursively
python chronohash.py hash ~/storage/downloads -r

# Save checksums to a file
python chronohash.py hash ~/storage/downloads -r -o checksums.txt

# Script-friendly output
python chronohash.py hash file.zip --json
python chronohash.py hash file.zip --plain
~~~

### verify

~~~
python chronohash.py verify FILE EXPECTED_HASH [-a ALGO]
python chronohash.py verify -c CHECKFILE [-a ALGO]
~~~

| Option                    | Description                                         |
|---------------------------|-----------------------------------------------------|
| `-c`, `--checkfile FILE`  | Verify every entry in a checksum file               |
| `-a`, `--algo ALGO`       | Force an algorithm (default: detect from length)    |

Auto-detected lengths: 32 = md5, 40 = sha1, 64 = sha256, 128 = sha512. For `sha3_256` or `blake2b`, pass `-a`.

Examples:

~~~bash
# Check a download against the hash published by the vendor
python chronohash.py verify app.apk 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08

# Verify everything listed in a checksum file
python chronohash.py verify -c checksums.txt
~~~

Checksum file format (same as `sha256sum`):

~~~
<hash>  <filename>
~~~

Filenames are resolved relative to the checksum file's folder. Blank lines and lines starting with `#` are ignored.

### compare

~~~
python chronohash.py compare A B [-a ALGO]
~~~

Both arguments must be files, or both must be folders.

~~~bash
# Two files
python chronohash.py compare original.bin suspect.bin

# Two folders (shows CHANGED / ONLY IN A / ONLY IN B)
python chronohash.py compare ./backup ./current
~~~

## Exit codes

| Code | Meaning                                  |
|------|------------------------------------------|
| 0    | Success / all checks passed / identical  |
| 1    | Mismatch, differences found, or errors   |
| 2    | Usage error (bad arguments, missing file)|
| 130  | Interrupted with Ctrl+C                  |

Use them in scripts:

~~~bash
if python chronohash.py verify -c checksums.txt -q; then
  echo "Backup intact"
else
  echo "Backup corrupted!"
fi
~~~

## Troubleshooting

| Problem                                | Fix                                                                 |
|----------------------------------------|---------------------------------------------------------------------|
| `ModuleNotFoundError: No module named 'rich'` | Run `pip install -r requirements.txt`                        |
| `python: command not found`            | Run `pkg install python`                                            |
| Box characters show as `?`             | Install a different Termux font: `pkg install termux-styling`       |
| Banner shows compact text only         | Screen under 62 columns. Rotate to landscape or zoom out            |
| `Permission denied` on phone files     | Run `termux-setup-storage` and allow storage access                 |
| `No such file or directory`            | Check the path. Use `ls` to confirm the file exists                 |

## Project structure

~~~
chronohash/
├── chronohash.py
├── requirements.txt
└── README.md
~~~

## Skills demonstrated

- CLI design with `argparse` subcommands
- Streaming file I/O
- `hashlib` and `hmac` (constant-time comparison)
- Terminal UI with `rich`
- Scriptable exit codes

## Part of the CHRONO SUITE

A growing toolkit of defensive security and developer utilities. All tools share the same look and CLI conventions.

## Disclaimer

For legal, defensive and educational use on systems you own or are authorized to test. The author is not responsible for misuse.

## License

MIT

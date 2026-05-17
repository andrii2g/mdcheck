# mdcheck

`mdcheck` is a Python CLI that scans a folder for Markdown files, extracts links, validates local targets and optional HTTP(S) URLs, and produces a Markdown report.

## Features

- Recursively discovers `.md` and `.markdown` files.
- Extracts inline links, image links, autolinks, and parser-resolved reference links.
- Validates local file targets and Markdown anchors.
- Validates HTTP and HTTPS URLs unless URL checks are disabled.
- Writes a Markdown report to stdout or to a file.

## Install From Source

Recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

For development tools:

```bash
python -m pip install -e ".[dev]"
```

On Debian/Ubuntu, system Python is often externally managed, so `python3 -m pip install -e .` outside a virtual environment can fail with a PEP 668 error. If needed, install the required system packages first:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip
```

If `python3 -m venv .venv` is unavailable, install:

```bash
sudo apt install -y python3-full
```

## Usage

```bash
mdcheck PATH
mdcheck PATH --no-url-check
mdcheck PATH --report mdcheck-report.md
mdcheck --version
```

Examples:

```bash
mdcheck .
mdcheck ./docs
mdcheck ./docs --no-url-check
mdcheck ./docs --report reports/mdcheck.md
```

## Supported Link Types

- Markdown inline links: `[Text](target)`
- Markdown images: `![Alt](target)`
- Autolinks: `<https://example.com>`
- Parser-resolved reference links

Target handling:

- Local targets such as `./guide.md`, `../assets/logo.png`, `/docs/index.md`, and `#intro`
- HTTP and HTTPS URLs
- `mailto:` links are accepted without remote validation
- Unsupported schemes such as `javascript:` and `tel:` produce unsupported-scheme findings when parsed as links

## Exit Codes

- `0`: no findings
- `1`: one or more findings
- `2`: CLI usage error or runtime error

## Report Output

Default output is Markdown written to stdout.

With `--report PATH`, `mdcheck` writes the full Markdown report to that file and prints a short summary to stdout.

## Known Limitations

- ATX headings only for anchor extraction
- No Setext heading support
- No custom heading ID support such as `{#custom-id}`
- No config file
- No include/exclude CLI options
- No concurrent URL validation
- No JSON or SARIF output
- No GitHub Action wrapper
- No browser-based JavaScript rendering

## CLI Contract

The v0.1 CLI exposes only:

- `--report PATH`
- `--no-url-check`
- `--verbose`
- `--version`
- `-h`, `--help`

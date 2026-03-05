# airtable-cli

A command-line tool for interacting with the [Airtable Web API](https://airtable.com/developers/web/api/introduction). Manage bases, tables, fields, records, comments, and webhooks from your terminal — with interactive fuzzy-search prompts or fully non-interactive scripting mode.

## Requirements

- Python 3.10+

## Installation

**via pip** (simplest):
```bash
pip install airtable-cli
```

**via pipx** (recommended — isolates the tool from your system Python):
```bash
pipx install airtable-cli
```

**via Homebrew** (macOS/Linux):
```bash
brew tap professor-eggs/airtable-cli
brew install airtable-cli
```

**from source** (development):
```bash
git clone https://github.com/professor-eggs/airtable-cli
cd airtable-cli
pip install -e ".[dev]"
```

## Authentication

Get a Personal Access Token from [airtable.com/create/tokens](https://airtable.com/create/tokens), then configure the CLI:

```bash
airtable auth configure --token patXXXXXXXXXXXXXX
```

You can also set the token via environment variable (takes precedence over the config file):

```bash
export AIRTABLE_PAT=patXXXXXXXXXXXXXX
```

The config file is stored at `~/.config/airtable-cli/config.toml`.

## Usage

```
airtable [--base TEXT] [--output table|json|yaml] [--no-interactive] [--version]
```

| Flag | Description |
|------|-------------|
| `--base` | Override the default base ID for this invocation (env: `AIRTABLE_BASE_ID`) |
| `--output`, `-o` | Output format: `table` (default), `json`, or `yaml` |
| `--no-interactive` | Disable all prompts — required args must be passed as flags |
| `--version` | Print version and exit |

## Command Reference

### `auth`

```bash
airtable auth configure [--token TEXT] [--default-base TEXT]
airtable auth show
airtable auth revoke
```

### `bases`

```bash
airtable bases list
airtable bases schema [--base TEXT]
```

### `tables`

```bash
airtable tables list   [--base TEXT]
airtable tables get    [--base TEXT] [--table TEXT]
airtable tables create [--base TEXT] [--name TEXT] [--description TEXT] [--fields JSON]
```

### `fields`

```bash
airtable fields list   [--base TEXT] [--table TEXT]
airtable fields create [--base TEXT] [--table TEXT] [--name TEXT] [--type TEXT] [--options JSON]
airtable fields update [--base TEXT] [--table TEXT] [--field TEXT] [--name TEXT] [--options JSON]
```

### `records`

```bash
airtable records list   [--base TEXT] [--table TEXT] [--view TEXT] [--filter TEXT]
                        [--sort FIELD:asc|desc]... [--max-records INT]
                        [--fields TEXT]... [--all-pages] [--cell-format json|string]
airtable records get    [--base TEXT] [--table TEXT] [--record TEXT]
airtable records create [--base TEXT] [--table TEXT] [--fields JSON] [--fields-file PATH] [--typecast]
airtable records update [--base TEXT] [--table TEXT] [--record TEXT]...
                        [--fields JSON] [--fields-file PATH] [--mode patch|put] [--typecast]
airtable records delete [--base TEXT] [--table TEXT] [--record TEXT]... [--confirm/--no-confirm]
```

### `comments`

```bash
airtable comments list   [--base TEXT] [--table TEXT] [--record TEXT]
airtable comments create [--base TEXT] [--table TEXT] [--record TEXT] [--text TEXT]
airtable comments delete [--base TEXT] [--table TEXT] [--record TEXT] [--comment TEXT] [--confirm/--no-confirm]
```

### `webhooks`

```bash
airtable webhooks list     [--base TEXT]
airtable webhooks create   [--base TEXT] [--url TEXT] [--filters JSON] [--specification JSON]
airtable webhooks update   [--base TEXT] [--webhook TEXT] [--enable/--disable] [--refresh-expiry]
airtable webhooks delete   [--base TEXT] [--webhook TEXT] [--confirm/--no-confirm]
airtable webhooks payloads [--base TEXT] [--webhook TEXT] [--cursor INT]
```

## Examples

```bash
# Configure auth and set a default base
airtable auth configure --token patXXX --default-base appXXXXXXXX

# List all bases as JSON
airtable --output json bases list

# List tables in a base
airtable --base appXXXXXXXX tables list

# List all records across all pages
airtable --base appXXXXXXXX records list --table tblXXXXXXXX --all-pages

# Filter and sort records
airtable --base appXXX records list --table tblXXX \
  --filter "Status = 'Active'" \
  --sort "Name:asc" \
  --output json

# Create a single record
airtable --base appXXX records create --table tblXXX \
  --fields '{"Name": "Alice", "Status": "Active"}'

# Bulk create from a JSON file
echo '[{"Name": "Foo"}, {"Name": "Bar"}]' > records.json
airtable --base appXXX records create --table tblXXX --fields-file records.json

# Update a record
airtable --base appXXX records update --table tblXXX \
  --record recXXXXXXXXXXXXXX \
  --fields '{"Status": "Done"}'

# Delete records without confirmation prompt
airtable --no-interactive --base appXXX records delete \
  --table tblXXX \
  --record recAAA --record recBBB \
  --no-confirm

# Create a webhook
airtable --base appXXX webhooks create --url https://example.com/hook

# Disable a webhook
airtable --base appXXX webhooks update --webhook whdXXX --disable

# Script-friendly: pipe JSON output
airtable --no-interactive --output json --base appXXX records list --table tblXXX \
  | jq '.[].fields.Name'
```

## Interactive Mode

When a required argument is missing and the terminal is interactive (TTY), the CLI automatically prompts with fuzzy-search pickers — for example, selecting a base by name or picking a record from a list. Pass `--no-interactive` to suppress all prompts and require every argument as a flag.

## Configuration File

`~/.config/airtable-cli/config.toml`

```toml
[auth]
token = "patXXXXXXXXXXXXXX"

[defaults]
base_id = "appXXXXXXXX"

[output]
format = "table"
color = true
```

Environment variables `AIRTABLE_PAT` and `AIRTABLE_BASE_ID` take precedence over the config file.

## Rate Limiting

The client uses a token bucket (5 requests/second) and automatically retries on HTTP 429 responses with exponential backoff (up to 3 retries).

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

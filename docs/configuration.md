# Configuration and imports

[Back to README](../README.md)

Run the commands in this guide from the repository root after completing the
[quick start](../README.md#quick-start).

## Use your own statements


Remove the copied demo CSV before importing real data. Place supported statement
CSVs in account folders under `data/raw/`, for example:

```text
data/raw/
  debit_main/2026/february.csv
  credit_main/2026/february.csv
  venmo/2026/february.csv
```

Set the reporting year, month, categories, and budget fractions in `config.toml`.
Edit `category.toml` to match your merchants and account folder names; the
example's account-specific rules use `debit_demo` and `credit_demo`.
Then run `python -m bb` again. Review `uncategorized` transactions and add rules
as needed. See [Import Conventions](#import-conventions) for supported formats.

Local configuration, statements, and generated workbooks are ignored by Git.
Terminal reports contain transaction details, so use fictional data for demos
and screenshots. See [Privacy and development](development.md#privacy-and-development).


## Import Conventions

Raw statement exports live under `data/raw/<account-name>/<year>/<month>.csv`.

Parser selection is directory-driven:

- `debit*`: Chase debit statement CSV
- `credit*`: Chase credit-card statement CSV
- `venmo`: Venmo account statement CSV

## Current command

Run the monthly budget summary for the configured month:

```bash
python -m bb
```

The CLI:

- loads all imported transactions
- filters to the configured `monthly_budget.year` and `monthly_budget.month`
- categorizes the selected month using `category.toml`
- prints a monthly summary with income, bucket totals, category totals, and
  needs / wants / savings percentages

## Configuration

The config file shape is:

```toml
raw_data_path = "data/raw"

[monthly_budget]
year = 2026
month = "february"

[monthly_budget.needs]
frac = 0.5
categories = ["rent", "groceries"]

[monthly_budget.wants]
frac = 0.3
categories = ["restaurants", "movies"]

[monthly_budget.savings]
frac = 0.2
categories = ["savings"]
```

See [config.example.toml](../config.example.toml) for a generic example.

The monthly budget config does two jobs:

- it selects the reporting month
- it defines the budget taxonomy and target fractions for `needs`, `wants`,
  and `savings`

Categorization rules are based on the tracked template
[category.example.toml](../category.example.toml). Copy it to `category.toml` and
edit `category.toml` locally.

## Monthly Filtering

Monthly filtering uses each transaction's normalized `posting_date`.

- Chase debit: filters by `Posting Date`
- Chase credit: filters by `Post Date`
- Venmo: filters by the date portion of `Datetime`

Filtering does not use filenames or directory names for month logic. Those are
only used for parser routing and file organization.

Supported `monthly_budget.month` syntax:

- month names, case-insensitive: `"february"`, `"February"`, `"FEBRUARY"`
- numeric strings: `"2"`
- integers: `2`

Valid month numbers are `1` through `12`.

Examples:

```toml
[monthly_budget]
year = 2026
month = "february"
```

```toml
[monthly_budget]
year = 2026
month = "2"
```

```toml
[monthly_budget]
year = 2026
month = 2
```


## Export settings

By default, each run regenerates `exports/<year>.xlsx` with twelve monthly
worksheets. Customize the output in `config.toml`:

```toml
[monthly_budget.export]
regenerate = true
path = "exports"
```

Set `regenerate = false` to print reports without rewriting the workbook.
A path with a filename suffix is treated as a file and saved with an `.xlsx`
extension; a directory path receives `<year>.xlsx`. Relative paths resolve
from the repository root. Keep output in an ignored directory.

## Windows setup

In PowerShell, create and activate the environment with:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
git config core.hooksPath .githooks
Copy-Item config.example.toml config.toml
Copy-Item category.example.toml category.toml
New-Item -ItemType Directory -Force data/raw/debit_demo/2026
Copy-Item tests/fixtures/chase_debit_february.csv data/raw/debit_demo/2026/february.csv
python -m bb
```

Use these commands in a fresh clone; preserve existing local configuration.

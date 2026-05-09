# Budget-Bot
I'm tired of tallying up my budget, so I'm building this repo to do it for me

## Current command

Calculate income from all imported transactions with a positive amount:

```bash
python -m src.bb
```

The current income report applies the configured monthly filter and prints a
header like `Income for 2026-02: ...`.

## Configuration

The config file shape is:

```toml
raw_data_path = "data/raw"

[monthly_budget]
year = 2026
month = "february"
```

See [config.example.toml](config.example.toml) for a generic example.

Categorization rules live in [category.toml](category.toml). They are kept out
of Python so categories and matching rules stay user-editable.

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

## Import Conventions

Raw statement exports live under `data/raw/<account-name>/<year>/<month>.csv`.

Parser selection is directory-driven:

- `debit*`: Chase debit statement CSV
- `credit*`: Chase credit-card statement CSV
- `venmo`: Venmo account statement CSV

Each importer must normalize rows into the shared `Transaction` model with:

- `account`
- `source_file`
- `posting_date`
- `description`
- `amount`
- `source_metadata`

Source-specific fields belong in `source_metadata`, not in the top-level model.

The loader also validates the CSV columns for each directory. If you add a new
account source, you need to:

1. Add a parser and expected-column definition in `src/bb/transaction.py`.
2. Teach `get_statement_parser()` and `get_expected_columns()` how to route the new account directory.
3. Add fixture coverage in `tests/fixtures/` and parser tests in `tests/test_statement_parsers.py`.

## Categorization Rules

Categorization rules are defined in [category.toml](category.toml), not in
Python source.

- `category.toml` is the user-controlled rules file.
- Rules are evaluated in order.
- The first matching rule wins.

# Budget-Bot
I'm tired of tallying up my budget, so I'm building this repo to do it for me

## Current command

Calculate income from all imported transactions with a positive amount:

```bash
python -m src.bb
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

1. Add a parser and expected-column definition in `src/bb/transactions.py`.
2. Teach `get_statement_parser()` and `get_expected_columns()` how to route the new account directory.
3. Add fixture coverage in `tests/fixtures/` and parser tests in `tests/test_statement_parsers.py`.

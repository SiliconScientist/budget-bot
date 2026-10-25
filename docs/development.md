# Privacy and development

[Back to README](../README.md)

## Privacy and development

Keep real statements under `data/` and generated workbooks under `exports/`
or `data/`. Both directories are ignored, along with local `config.toml`,
`category.toml`, environment files, and common financial export formats.
Never force-add private files. Ignore rules do not remove files already in Git.

Install the local commit guard after cloning:

```bash
git config core.hooksPath .githooks
```

The guard checks **staged content**, rejects private file paths, and catches
common credentials, account suffixes, bank references, and personal emails.
GitHub Actions repeats the check on pushes and pull requests. CI runs after
upload, so the local guard and staged-diff review are the first line of defense.

All checked-in fixtures use fictional identities and financial values.
Use account labels such as `debit_demo` and `credit_demo`. Never build a fixture
by copying a real statement and merely changing its names. CSV fixtures must
match the SHA-256 hashes in `tests/fixtures/synthetic-manifest.json`; update a
hash only after reviewing the entire fixture as synthetic.

Before committing, run `git diff --cached` and `python3 scripts/check_privacy.py`.
Review fixture and manifest changes together. Hooks can be bypassed, and these
checks cannot recognize every kind of personal information.

The CLI prints private transaction details when run with real data. Use only
synthetic data for screenshots, demos, issue reports, and CI. Enable GitHub
secret scanning and push protection when available; credential detection does
not replace review of financial information.


## Adding an importer

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

1. Add a parser and expected-column definition in `src/bb/parse.py`.
2. Teach `get_statement_parser()` and `get_expected_columns()` how to route the new account directory.
3. Add fixture coverage in `tests/fixtures/` and parser tests in `tests/test_parse.py`.


## Running checks

From the repository root with the virtual environment activated:

```bash
python -m unittest discover -s tests -q
python scripts/check_privacy.py
git diff --cached
```

The privacy check reads the Git index, so stage intended changes before using
it to review a commit. Use only fictional data in tests.

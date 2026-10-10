# Budget-Bot
I'm tired of tallying up my budget, so I'm building this repo to do it for me

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

## Current command

Run the monthly budget summary for the configured month:

```bash
python -m src.bb
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

See [config.example.toml](config.example.toml) for a generic example.

The monthly budget config does two jobs:

- it selects the reporting month
- it defines the budget taxonomy and target fractions for `needs`, `wants`,
  and `savings`

Categorization rules are based on the tracked template
[category.example.toml](category.example.toml). Copy it to `category.toml` and
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

## Budgeting Workflow

1. Define your monthly taxonomy and target fractions in `config.toml`.
2. Assign merchants and transaction patterns to categories in `category.toml`.
3. Run `python -m src.bb` for the selected month.
4. Interpret the summary:
   `Needs`, `Wants`, and `Savings` each show target %, actual %, and dollars.
5. Review the category breakdown under each bucket and fix any missing rules or
   uncategorized spend.

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

## Categorization

Categorization rules are defined in TOML, not in Python source.

- [category.example.toml](category.example.toml) is the tracked example.
- `category.toml` is your local working rules file.
- `category.toml` is gitignored so you can customize it without committing
  personal rules by accident.

## Categorization Workflow

1. Importers normalize raw CSV rows into `Transaction` objects.
2. The app loads rules from `category.toml` when present, otherwise it falls
   back to `category.example.toml`.
3. Rules are evaluated top to bottom.
4. The first matching rule assigns the category.
5. If nothing matches, the transaction is labeled `uncategorized`.

The CLI also prints a simple categorization inspection report showing each
transaction's monthly budget summary.

## Rule File Location

The files are:

```text
category.example.toml
category.toml
```

Both live at the repo root.

- `category.example.toml`: tracked template
- `category.toml`: local override, intended to be user-edited directly

Typical setup:

```bash
cp category.example.toml category.toml
```

## Rule Format

Each rule is a TOML table in the top-level `rules` array:

```toml
[[rules]]
id = "paycheck_income"
bucket = "income"
category = "paycheck"
description_contains = ["PAYROLL"]
is_income = true
```

Required fields:

- `id`: unique rule identifier
- `category`: snake_case category id assigned when the rule matches, such as `rent` or `tuition_education`

Optional classification fields:

- `bucket`: snake_case bucket id such as `needs`, `wants`, `savings`, `income`, or `transfers`

Optional match fields:

- `accounts`: array of account names such as `["debit_demo"]` or `["venmo"]`
- `description_contains`: array of substrings; any one match is enough
- `details`: array matched against `transaction.source_metadata["details"]`
- `transaction_types`: array matched against `transaction.source_metadata["transaction_type"]`
- `is_income`: `true` or `false`

Optional explicit flow flags:

- `credit_card_payment = true`
- `venmo_reimbursement = true`
- `internal_transfer = true`

All configured fields on a rule must match for that rule to win.

Category and bucket ids are stored as machine-friendly snake_case in config and
code. User-facing labels should be derived at output time.

## Precedence

Rules are ordered. Earlier rules win.

That means specific rules should come before broad catch-all rules. For
example, this is correct:

```toml
[[rules]]
id = "debit_coffee"
bucket = "wants"
category = "restaurants"
accounts = ["debit_demo"]
description_contains = ["COFFEE"]

[[rules]]
id = "debit_card_general"
bucket = "wants"
category = "hobbies"
transaction_types = ["DEBIT_CARD"]
```

`CARD PURCHASE COFFEE` on `debit_demo` will be categorized as
`restaurants`, not `hobbies`, because the first rule matches first.

## Fallback Behavior

If no rule matches, the transaction is categorized as:

```text
uncategorized
```

In that case there is no matched rule id.

## Examples

Paycheck rule:

```toml
[[rules]]
id = "paycheck_income"
bucket = "income"
category = "paycheck"
description_contains = ["PAYROLL"]
is_income = true
```

Account-specific coffee rule:

```toml
[[rules]]
id = "debit_coffee"
bucket = "wants"
category = "restaurants"
accounts = ["debit_demo"]
description_contains = ["COFFEE"]
```

Chase credit payment rule:

```toml
[[rules]]
id = "credit_card_payment"
bucket = "transfers"
category = "credit_card_payment"
accounts = ["credit_demo"]
credit_card_payment = true
```

Venmo reimbursement rule:

```toml
[[rules]]
id = "venmo_reimbursement"
bucket = "income"
category = "reimbursement"
accounts = ["venmo"]
venmo_reimbursement = true
```

Internal transfer rule:

```toml
[[rules]]
id = "internal_transfer"
bucket = "transfers"
category = "internal_transfer"
internal_transfer = true
```

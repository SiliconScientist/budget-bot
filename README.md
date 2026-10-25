# Budget Bot

A Python CLI for categorizing Chase and Venmo transactions, comparing monthly
spending against budget targets, and exporting annual Excel reports.

## Why needs, wants, and savings?

Budget Bot grew out of a practical goal: make it easier to understand where
money goes and whether everyday spending leaves room for future goals. Its
budget structure reflects three priorities: cover essential expenses, make
deliberate choices about discretionary spending, and reserve money for the
future. Categorizing transactions makes those priorities visible in the numbers.

The default targets follow the familiar **50/30/20 budgeting framework**:

- **Needs — 50%:** essentials such as housing, groceries, utilities, and transportation.
- **Wants — 30%:** discretionary spending such as dining out, entertainment, and hobbies.
- **Savings — 20%:** room for financial goals, such as an emergency fund or longer-term savings.

This framework is a starting point for organizing a budget. The Consumer
Financial Protection Bureau describes it in its
[budgeting materials](https://www.consumerfinance.gov/consumer-tools/educator-tool/youth-financial-education/teach/activities/analyzing-budgets/).
Budget Bot lets you change both the target percentages and the categories in
each bucket to reflect your circumstances. The three target fractions must
add up to 100%.

## What Budget Bot does

Budget Bot turns exported statements into a repeatable monthly review. Instead
of manually sorting every purchase each month, you define rules once and refine
them as new transactions appear.

- **Brings supported accounts together.** Imports Chase checking/debit,
  Chase credit-card, and Venmo CSV statements into a common transaction format.
  It checks statement columns and includes only completed Venmo transactions.
- **Categorizes transactions with rules you control.** Match descriptions,
  account names, amounts, bank categories, or transaction types. Rules run in
  order, with the first match winning, so specific exceptions can come before
  broader rules. For example, different amounts paid to the same recipient
  can be assigned to rent and utilities separately.
- **Makes classification reviewable.** The transaction report shows the
  assigned category and matching rule. Unmatched transactions remain labeled
  `uncategorized`, making it clear where more review is needed.
- **Separates different kinds of money movement.** Rules can identify credit-card
  payments, internal transfers, and Venmo reimbursements. You can also mark
  positive transactions as other inflows instead of budget income, so the
  income figure reflects the definition you choose.
- **Compares plans with actual spending.** Filters by posting date for the
  selected month, then reports income, other inflows, category totals, and
  needs / wants / savings targets alongside actual dollar amounts and percentages.
- **Creates a year of reports.** Exports an Excel workbook with a worksheet for
  each month, using the configured categories and targets. Processing runs
  locally on your statement files; no bank login is required.

### How to read the savings figure

The current report calculates savings as **budget income + other inflows − needs
spending − wants spending**. This is a calculated remainder, not a measurement
of deposits into a savings account. Spending assigned to other buckets, including
`uncategorized`, is not subtracted from that figure. Review unmatched transactions
and your transfer/income rules before interpreting it as money available to save.
When needs and wants exceed total inflows, the remainder can be negative.

## Quick start

Requires **Python 3.12 or newer** and Git. The commands below use macOS/Linux
shell syntax and run a demo with fictional transactions.

### 1. Install

```bash
git clone https://github.com/SiliconScientist/budget-bot.git
cd budget-bot
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
git config core.hooksPath .githooks
```

If your Python 3.12+ interpreter has a different name, substitute it for
`python3.12`. On Windows PowerShell, create the environment with
`py -3.12 -m venv .venv` and activate it with `.venv\Scripts\Activate.ps1`.

### 2. Configure and load the demo

From the repository root:

```bash
cp config.example.toml config.toml
cp category.example.toml category.toml
mkdir -p data/raw/debit_demo/2026
cp tests/fixtures/chase_debit_february.csv data/raw/debit_demo/2026/february.csv
```

The example config selects February 2026 and sets needs / wants / savings
targets of 50% / 30% / 20%. If you already have local configuration files,
keep them instead of overwriting them with the copy commands above.

### 3. Run

```bash
python -m bb
```

You'll see a monthly budget summary and a transaction categorization report.
The demo also creates `exports/2026.xlsx`, with one worksheet per month.
Months without imported transactions have no activity to report.

### Use your own statements

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
and screenshots. See [Privacy and development](#privacy-and-development).

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
3. Run `python -m bb` for the selected month.
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
- `amounts`: array of exact signed amounts as strings, such as `["-1000.00"]`

Income reporting:

- `counts_toward_income`: defaults to `true`; set it to `false` to report a
  matching positive transaction under other inflows instead of budget income.

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

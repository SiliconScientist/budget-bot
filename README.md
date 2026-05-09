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
transaction, its assigned category, and the matched rule id.

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
category = "dining:coffee"
accounts = ["debit_demo"]
description_contains = ["COFFEE"]

[[rules]]
id = "debit_card_general"
category = "spending:card"
transaction_types = ["DEBIT_CARD"]
```

`CARD PURCHASE COFFEE` on `debit_demo` will be categorized as
`dining:coffee`, not `spending:card`, because the first rule matches first.

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
category = "Income"
description_contains = ["PAYROLL"]
is_income = true
```

Account-specific coffee rule:

```toml
[[rules]]
id = "debit_coffee"
category = "dining:coffee"
accounts = ["debit_demo"]
description_contains = ["COFFEE"]
```

Chase credit payment rule:

```toml
[[rules]]
id = "credit_card_payment"
category = "transfer:credit-card-payment"
accounts = ["credit_demo"]
credit_card_payment = true
```

Venmo reimbursement rule:

```toml
[[rules]]
id = "venmo_reimbursement"
category = "income:reimbursement"
accounts = ["venmo"]
venmo_reimbursement = true
```

Internal transfer rule:

```toml
[[rules]]
id = "internal_transfer"
category = "transfer:internal"
internal_transfer = true
```

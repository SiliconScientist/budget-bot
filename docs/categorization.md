# Categorization rules

[Back to README](../README.md)

## Categorization

Categorization rules are defined in TOML, not in Python source.

- [category.example.toml](../category.example.toml) is the tracked example.
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

The CLI also prints a transaction report showing each transaction's category
and matching rule, alongside the monthly budget summary.

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

All configured match conditions must hold for a rule to win. Classification
fields and `counts_toward_income` control the result rather than matching inputs.

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

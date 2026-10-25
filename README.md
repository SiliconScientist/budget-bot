# Budget Bot

A Python CLI for categorizing Chase and Venmo transactions, comparing monthly
spending against budget targets, and exporting annual Excel reports.

Budget Bot makes a monthly financial review easier: cover essentials, spend
intentionally, and leave room for future goals. Its default **50% needs / 30%
wants / 20% savings** targets and spending categories are fully configurable.
Read more about the [budgeting approach](docs/budgeting.md).

## What it does

- Imports Chase checking, Chase credit-card, and Venmo CSV statements.
- Applies customizable rules and shows how each transaction was categorized.
- Distinguishes income, other inflows, and transfers according to your rules.
- Compares monthly spending with budget targets and exports a year of Excel reports.

Everything runs locally on your statement files; no bank login is required.

## Quick start

Requires **Python 3.12+** and Git. Try the included fictional data in a fresh
clone (macOS/Linux commands below; [Windows setup](docs/configuration.md#windows-setup)):

```bash
git clone https://github.com/SiliconScientist/budget-bot.git
cd budget-bot
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
git config core.hooksPath .githooks

cp config.example.toml config.toml
cp category.example.toml category.toml
mkdir -p data/raw/debit_demo/2026
cp tests/fixtures/chase_debit_february.csv data/raw/debit_demo/2026/february.csv

python -m bb
```

Use the name of your Python 3.12+ interpreter if it differs from `python3.12`.
If you already have local configuration files, preserve them instead of running
the configuration copy commands.

You'll get a February 2026 budget summary, a transaction report, and
`exports/2026.xlsx` with twelve monthly worksheets.
[Import your own statements](docs/configuration.md#use-your-own-statements)
when you're ready; remove the copied demo CSV first.

The reported savings figure is a calculated remainder, not a savings-account
balance. Review uncategorized spending and
[how the calculation works](docs/budgeting.md#how-to-read-the-savings-figure).

## Documentation

- [Budgeting and reports](docs/budgeting.md) — principles, features, and interpreting results.
- [Configuration and imports](docs/configuration.md) — your statements, reporting month, targets, and exports.
- [Categorization rules](docs/categorization.md) — matching, precedence, income handling, and examples.
- [Privacy and development](docs/development.md) — private data safeguards, tests, and adding importers.

Local configuration, statements, and exports are ignored by Git. Terminal
reports contain transaction details; use fictional data for shared demos.

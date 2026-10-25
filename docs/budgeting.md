# Budgeting and reports

[Back to README](../README.md)

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

## Budgeting Workflow

1. Define your monthly taxonomy and target fractions in `config.toml`.
2. Assign merchants and transaction patterns to categories in `category.toml`.
3. Run `python -m bb` for the selected month.
4. Interpret the summary:
   `Needs`, `Wants`, and `Savings` each show target %, actual %, and dollars.
5. Review the category breakdown under each bucket and fix any missing rules or
   uncategorized spend.

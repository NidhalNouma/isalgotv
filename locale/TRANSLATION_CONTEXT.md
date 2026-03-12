# IsAlgo Translation Context

## Purpose
This document is the translation context for the IsAlgo platform. It is meant to help translators (human or AI) produce consistent, accurate, and domain-correct translations across all locale catalogs in `locale/*/LC_MESSAGES/django.po`.

Always cross-reference the approved terminology in `locale/TRANSLATION_GLOSSARY.csv` before choosing a term — it contains ~80 vetted translations across all supported languages organized by domain (brand, technical, ui, auth, billing, marketplace, trading, automation, performance, ai, legal).

## What This Project Is
IsAlgo is a multilingual trading platform with three main user-facing products:
- Strategy marketplace for TradingView-based strategies.
- Trade automation engine that connects user broker accounts and executes actions from webhook alerts.
- AI assistant/chat area (Tero) with chat sessions, token-based usage, and account integrations.

The platform targets retail and professional traders and supports multiple brokers, exchanges, and account types (crypto, forex, and related services).

## Core User Areas
- Public marketing and landing pages.
- Authentication and account lifecycle (register, login, password reset).
- User profile and account settings.
- Membership and subscription billing (Stripe).
- Strategy pages (discover, detail, comments, reports, votes, subscriptions).
- Automation pages (connect broker, view logs/trades, close trade, manage status).
- Performance and analytics pages.
- Documentation and legal pages.
- Tero AI chat and token purchase flows.
- **Transactional emails** (see "Categories of Translatable Content" below).

## Main Features To Keep In Mind During Translation
- Multi-language UI for a large Django web application.
- Financial and trading terminology in UI labels and help text.
- Broker-specific setup and troubleshooting documentation.
- Payment, plan, and subscription terminology.
- Notification and transactional email language.
- Legal content (disclaimer, terms of use, privacy policy).
- AI chat product language (sessions, messages, response streaming, token usage).

## Internationalization Scope
Configured languages:
- English (`en`) — source language.
- French (`fr`).
- Spanish (`es`).
- German (`de`).
- Chinese Simplified (`zh_Hans`, locale code rendered as `zh-hans` in settings).
- Japanese (`ja`).
- Arabic (`ar`).
- Russian (`ru`).

Translation files:
- Source: `locale/<lang>/LC_MESSAGES/django.po`
- Compiled: `locale/<lang>/LC_MESSAGES/django.mo`

As of the last update the catalog has **~2,265 entries** per language.

## Categories of Translatable Content
The PO files contain several distinct categories. Understanding these helps produce accurate translations:

1. **UI labels & buttons** — Short action text: "Log in", "Sign up", "Save", "Cancel", "Delete".
2. **Page headings & descriptions** — Marketing copy on landing and feature pages.
3. **Form fields & validation messages** — "Your Email", "Password", "This field is required."
4. **Email subjects** — Usually end with `- IsAlgo`. Keep them concise.
5. **Email body paragraphs** — Longer HTML-rich strings sent in transactional emails (account verification, password reset, payment confirmations, trade notifications, milestone alerts, strategy updates). These make up a significant portion of the catalog (~200+ entries).
6. **Email CTAs (calls to action)** — Button text inside emails: "Verify your email", "Reset password", "View your trades".
7. **Notification messages** — Alerts displayed in-app after actions.
8. **Error messages** — User-facing error strings.
9. **Legal & compliance text** — Disclaimers, terms of use, privacy policy content.
10. **Plural forms** — A small number of entries use `msgid_plural` / `msgstr[0]` / `msgstr[1]` for count-dependent text.

## Handling Special Syntax in PO Files

### Django template variables
Many strings contain placeholders like `%(name)s`, `%(strategy_name)s`, `%(amount)s`, `%(date)s`.
**These must be preserved exactly** in the translation — same name, same `%(...)s` syntax. Example:

```
msgid "Hello %(name)s, your trade on %(strategy_name)s was executed."
msgstr "Bonjour %(name)s, votre trade sur %(strategy_name)s a été exécuté."
```

### HTML tags
Roughly 60 entries contain inline HTML (`<strong>`, `<a href="...">`, `<br>`, `<p>`, etc.).
**Preserve all HTML tags and attributes exactly.** Only translate the visible text between tags:

```
msgid "Click <a href=\"%(url)s\">here</a> to verify your <strong>email</strong>."
msgstr "Cliquez <a href=\"%(url)s\">ici</a> pour vérifier votre <strong>email</strong>."
```

### Multi-line strings
Long strings in PO files are split across multiple lines:

```
msgid ""
"This is a very long string that has been "
"split across multiple lines in the PO file."
msgstr ""
"Ceci est une très longue chaîne qui a été "
"divisée sur plusieurs lignes dans le fichier PO."
```

Each continuation line is a quoted string. The quotes and line breaks must match the PO format.

### Escaped characters
Watch for escaped quotes (`\"`) and newlines (`\n`) inside msgid strings. Preserve them in the translation.

### Plural forms
A few entries use plural forms. Each language has its own plural rule (e.g., Arabic has 6 forms). Fill all `msgstr[N]` slots:

```
msgid "%(count)s strategy"
msgid_plural "%(count)s strategies"
msgstr[0] "%(count)s stratégie"
msgstr[1] "%(count)s stratégies"
```

### Fuzzy entries
Entries marked `#, fuzzy` are auto-suggested by Django and need human review. After verifying the translation is correct, remove the `#, fuzzy` flag. Use `make fuzzy` to list them.

## Product Domains And Terminology
Use domain-correct terms for these areas (see `TRANSLATION_GLOSSARY.csv` for approved translations):
- Trading concepts: entry, exit, position, stop loss, take profit, leverage, drawdown, PnL, risk, asset.
- Broker/exchange account concepts: API key, secret, account ID, wallet, base asset, quote asset, spot, futures.
- Automation concepts: webhook, alert, trigger, execution, logs, retries, status, active/inactive.
- Marketplace concepts: strategy, subscription, premium, report, comment, vote, author, seller.
- Billing concepts: plan, monthly/yearly/lifetime, payment method, invoice, coupon, refund, cancellation.
- AI concepts: chat session, message history, token usage, assistant response.

## Non-Translatable Terms (Keep As-Is)
Always preserve exact spelling/casing for brand, product, and protocol names unless a locale already has an approved equivalent in `TRANSLATION_GLOSSARY.csv`.

Examples:
- IsAlgo, Tero, TradingView, Stripe, Discord, Google
- API, Webhook, URL, JSON, ID, PnL
- cTrader, MetaTrader 4, MetaTrader 5, TradeLocker
- Binance, BinanceUS, Bybit, Bitget, BingX, MEXC, KuCoin, Kraken, OKX
- Apex, HyperLiquid, Coinbase, Deriv, Alpaca, Tastytrade

Notes:
- Do not transliterate broker names.
- Do not translate technical acronyms like API, URL, JSON, ID, PnL.

## Tone And Style
- Keep wording clear, concise, and action-oriented.
- Favor financial clarity over creative phrasing.
- Use neutral and professional tone for UI and docs.
- Use compliance-safe language in legal/billing contexts.
- Avoid slang.
- Preserve user trust by avoiding overpromising wording.
- Email subjects should be short and informative.
- Email body text should feel personal but professional — address the user directly.

## Translation Workflow

### Adding new translatable strings
1. Wrap new user-facing text with `{% trans "..." %}` (templates) or `_("...")` (Python).
2. Run `make messages` to extract strings into all PO files.
3. Run `make missing` to see which entries need translations.
4. Fill empty `msgstr ""` entries in each `locale/<lang>/LC_MESSAGES/django.po`.
5. Run `make fuzzy` to review auto-suggested translations and remove `#, fuzzy` flags for correct ones.
6. Run `make compile` to generate `.mo` files.
7. Restart the application to pick up the new `.mo` files.

### Bulk-filling translations (AI or script)
For large batches of missing translations:
1. Run `make export-missing lang=fr` — creates `locale/fr_missing.json` with all untranslated msgids (values are empty strings).
2. Fill in the translated values in the JSON file: `{ "source text": "translated text", ... }`.
3. Run `make fill lang=fr file=locale/fr_missing.json` to apply translations into the PO file.
4. Verify with `make stats` and `make missing`.
5. Compile with `make compile`.

### Handling fuzzy entries
Fuzzy entries (`#, fuzzy`) are auto-suggested translations that Django creates when source strings change. They are often wrong or misleading and must be reviewed before use. Django **ignores fuzzy entries at runtime** — they behave as if untranslated until the flag is removed.

To review and fix fuzzy entries in bulk:
1. Run `make fuzzy` to list all fuzzy entries per language.
2. Run `make export-fuzzy lang=fr` — creates `locale/fr_fuzzy.json` with each fuzzy msgid mapped to its current (likely wrong) msgstr.
3. Review and correct the translations in the JSON file.
4. Run `make fix-fuzzy lang=fr file=locale/fr_fuzzy.json` to replace msgstr values and remove the `#, fuzzy` flag.
5. Verify with `make fuzzy` (should show 0 fuzzy) and `make stats`.
6. Compile with `make compile`.

### Useful commands
Run `make help-translations` to see all available translation commands, or see the project `Makefile`.

Key commands:
- `make stats` — translated/total counts per language.
- `make missing` — list untranslated entries.
- `make fuzzy` — list fuzzy entries that need review.
- `make export-missing lang=<lang>` — export untranslated msgids to JSON.
- `make fill lang=<lang> file=<json>` — fill translations from JSON.
- `make export-fuzzy lang=<lang>` — export fuzzy entries to JSON.
- `make fix-fuzzy lang=<lang> file=<json>` — fix fuzzy entries from JSON.
- `make validate` — validate PO file syntax.
- `make overview` — full report (stats + missing + fuzzy).

## String Handling Rules
- Preserve placeholders exactly: `%s`, `%d`, `%(name)s`, `{name}`, `{}`, and HTML placeholders.
- Preserve punctuation used for variables or structured output.
- Preserve line breaks when meaningful (especially legal text and long docs).
- Preserve URL paths, code snippets, and command-like text.
- Do not alter template tags, variables, or HTML attributes.
- Keep capitalization rules for titles that start with `IsAlgo |`.

## Context-Sensitive Guidance
- Membership and payments:
  - Translate as subscription/billing language, not generic ecommerce language.
  - Keep plan names and brand references stable.
- Broker setup docs:
  - Prefer imperative instructions (for example: "Open", "Select", "Paste", "Confirm").
  - Keep exact field labels if they map to broker UI labels.
- Error and status messages:
  - Keep short, direct, and diagnostic.
  - Preserve any technical token (error code, status, or variable).
- Legal pages:
  - Keep formal register and legal precision.
  - Never simplify clauses if meaning can change.

## Consistency Checklist Before Finalizing A Locale
- Brand names remain unchanged.
- No placeholder corruption.
- No accidental translation of technical identifiers.
- Strategy and automation terms remain consistent across pages.
- Billing terms are consistent with Stripe flow language.
- Titles and navigation strings are consistent with existing style.
- Long legal/doc strings remain complete and structurally intact.

## Recommended Workflow
1. Run extraction for target language (`make messages-<lang>` or `make messages`).
2. Translate `msgstr` values with this context file as reference.
3. Run consistency checks for placeholders and brand names.
4. Compile catalogs (`make compile`).
5. Do UI spot-checks for critical flows:
   - Auth
   - Membership and payment
   - Strategy detail and subscribe
   - Automate broker setup and logs
   - Docs and legal pages
   - Tero chat pages

## Quick Architecture Snapshot (For Translators)
- Framework: Django monolith.
- i18n: Django `i18n_patterns` + locale `.po/.mo` catalogs.
- Async/background: Celery + Redis.
- Payment: Stripe.
- Frontend styling: Tailwind.
- Separate host/subdomain routes for main site, webhook endpoints, and Tero AI area.

## Source Of Truth
If a string is ambiguous, check where it is used in templates/views before translating. In this project, context can change meaning significantly between:
- strategy marketplace pages,
- broker automation flows,
- legal docs,
- AI chat interfaces.

---
Last updated: 2026-03-12
Maintainer intent: maximize translation quality and consistency for trading, billing, and AI product language.

---
name: translation-localization
description: "Translate and review IsAlgo locale catalogs with domain-accurate terminology, placeholder safety, and PO-file integrity across trading, billing, automation, legal, and AI chat content."
argument-hint: "Provide target language, file scope (full locale or specific entries), and whether you are translating missing strings, fixing fuzzy entries, or performing QA."
---

# IsAlgo Translation And Localization

## What This Skill Does

Use this skill to translate, review, and validate IsAlgo localization files with high consistency and zero syntax breakage.

This skill is optimized for:

- Django PO catalogs in `locale/<lang>/LC_MESSAGES/django.po`
- Trading, broker automation, billing, legal, and AI chat terminology
- Placeholder/HTML-safe translation updates
- Missing and fuzzy translation workflows

## When To Use

Use this skill when you need to:

- Translate new strings after extraction (`make messages`)
- Fill missing `msgstr` entries in one or more locales
- Review and fix `#, fuzzy` entries
- Validate terminology consistency against project glossary
- QA translation safety for placeholders, HTML tags, and plural forms

## Product Context

IsAlgo is a multilingual trading platform with three user-facing products:

- Strategy marketplace for TradingView-based strategies
- Trade automation with broker/exchange integrations via webhook alerts
- Tero AI chat area with token-based usage and account integrations

Primary user areas include auth, profile, subscriptions/billing, strategy pages, automation pages, performance pages, docs/legal pages, and transactional emails.

## Supported Locales

- English (`en`) source language
- French (`fr`)
- Spanish (`es`)
- German (`de`)
- Chinese Simplified (`zh_Hans`)
- Japanese (`ja`)
- Arabic (`ar`)
- Russian (`ru`)

## Source Of Truth Files

- Catalogs: `locale/<lang>/LC_MESSAGES/django.po`
- Compiled catalogs: `locale/<lang>/LC_MESSAGES/django.mo`
- Approved terminology: `.github/skills/translation-localization/TRANSLATION_GLOSSARY.csv`

Always cross-check term choices with the glossary before finalizing translations.

## Translation Safety Rules

### Preserve Placeholders Exactly

Never alter variable syntax or names:

- `%(name)s`, `%(strategy_name)s`, `%(amount)s`
- `%s`, `%d`
- `{name}`, `{}`

### Preserve HTML Structure Exactly

Keep tags and attributes unchanged (`<a href=...>`, `<strong>`, `<br>`, `<p>`, etc.).
Translate only user-visible text between tags.

### Preserve PO String Structure

- Keep multi-line quoted PO structure intact
- Preserve escaped characters such as `\"` and `\n`
- Keep punctuation and capitalization semantics where meaningful

### Handle Plurals Correctly

For entries with `msgid_plural`, fill every required `msgstr[N]` form for the target language.

### Handle Fuzzy Entries Explicitly

Treat `#, fuzzy` as untrusted suggestions requiring review.
After confirming correctness, remove fuzzy flags.

## Domain Terminology Priorities

Maintain domain-correct language for:

- Trading: entry, exit, stop loss, take profit, leverage, drawdown, PnL
- Broker accounts: API key, secret, wallet, base/quote asset, spot, futures
- Automation: webhook, trigger, execution, logs, retries, status
- Marketplace: strategy, premium, report, comment, vote, author, seller
- Billing: plan, invoice, coupon, refund, cancellation
- AI: chat session, token usage, assistant response

## Non-Translatable Terms

Keep these names/acronyms unchanged unless glossary explicitly says otherwise:

- Brands/products: IsAlgo, Tero, TradingView, Stripe, Discord, Google
- Acronyms/protocol terms: API, Webhook, URL, JSON, ID, PnL
- Broker/exchange names: Binance, Bybit, Bitget, BingX, MEXC, KuCoin, Kraken, OKX, Coinbase, Deriv, etc.

Do not transliterate broker names.

## Tone And Style

- Clear, concise, action-oriented wording
- Professional and neutral for UI/docs
- Compliance-safe wording for legal and billing
- Short, informative email subjects
- Personal but professional email body tone

## Standard Workflow

1. Extract strings with `make messages`.
2. Check missing entries with `make missing`.
3. Translate empty `msgstr` values using glossary-approved terms.
4. Review fuzzy entries with `make fuzzy` and fix/remove fuzzy flags.
5. Validate syntax with `make validate`.
6. Compile catalogs with `make compile`.
7. Spot-check key flows in UI.

## Bulk Workflow (JSON)

For missing entries:

1. `make export-missing lang=<lang>`
2. Fill generated JSON translations
3. `make fill lang=<lang> file=.github/skills/translation-localization/data/<lang>_missing.json`
4. `make stats` and `make missing`
5. `make compile`

For fuzzy entries:

1. `make export-fuzzy lang=<lang>`
2. Correct generated JSON translations
3. `make fix-fuzzy lang=<lang> file=.github/skills/translation-localization/data/<lang>_fuzzy.json`
4. `make fuzzy` and `make stats`
5. `make compile`

## QA Checklist

- Brand names preserved
- Placeholders untouched
- HTML tags/attributes untouched
- No technical identifiers mistranslated
- Trading/billing/automation terms consistent
- Legal text complete and precise
- Compiled successfully with no PO syntax errors

## Translation Categories To Handle Carefully

- UI buttons and labels
- Form validation messages
- In-app notifications and errors
- Transactional email subjects and HTML body content
- Legal/compliance text
- Pluralized strings

## Context-Aware Guidance

- Membership/payments: use subscription/billing language, not generic ecommerce language
- Broker setup docs: use imperative wording and keep field labels aligned with broker UI
- Error/status messages: short, direct, diagnostic
- Legal pages: formal register, preserve legal meaning exactly

## Architecture Snapshot For Translators

- Backend: Django monolith
- i18n: Django `i18n_patterns` + PO/MO catalogs
- Async: Celery + Redis
- Payments: Stripe
- Frontend: Tailwind

## Quick Prompts

- "Translate all missing French entries in django.po with placeholder-safe output and glossary consistency."
- "Review Arabic fuzzy entries and remove fuzzy flags only where wording is fully verified."
- "QA this locale file for placeholder corruption, HTML integrity, and terminology drift."

# IsAlgo Translation Context

## Purpose
This document is the translation context for the IsAlgo platform. It is meant to help translators (human or AI) produce consistent, accurate, and domain-correct translations across all locale catalogs in `locale/*/LC_MESSAGES/django.po`.

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
- English (`en`) - source language.
- French (`fr`).
- Spanish (`es`).
- German (`de`).
- Chinese Simplified (`zh_Hans`, locale code rendered as `zh-hans` in settings).
- Japanese (`ja`).
- Arabic (`ar`).
- Russian (`ru`).

Translation files:
- `locale/<lang>/LC_MESSAGES/django.po`
- Compiled output: `locale/<lang>/LC_MESSAGES/django.mo`

## Product Domains And Terminology
Use domain-correct terms for these areas:
- Trading concepts: entry, exit, position, stop loss, take profit, leverage, drawdown, PnL, risk, asset.
- Broker/exchange account concepts: API key, secret, account ID, wallet, base asset, quote asset, spot, futures.
- Automation concepts: webhook, alert, trigger, execution, logs, retries, status, active/inactive.
- Marketplace concepts: strategy, subscription, premium, report, comment, vote, author, seller.
- Billing concepts: plan, monthly/yearly/lifetime, payment method, invoice, coupon, refund, cancellation.
- AI concepts: chat session, message history, token usage, assistant response.

## Non-Translatable Terms (Keep As-Is)
Always preserve exact spelling/casing for brand, product, and protocol names unless a locale already has an approved equivalent.

Examples:
- IsAlgo
- Tero
- TradingView
- Stripe
- Discord
- Google
- API
- Webhook
- cTrader
- MetaTrader 4
- MetaTrader 5
- Binance
- BinanceUS
- Bybit
- Bitget
- BingX
- MEXC
- KuCoin
- Kraken
- OKX
- Apex
- HyperLiquid
- Coinbase
- TradeLocker
- Deriv
- Alpaca
- Tastytrade

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
Last updated: 2026-03-06
Maintainer intent: maximize translation quality and consistency for trading, billing, and AI product language.

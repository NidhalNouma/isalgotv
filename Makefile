# ──────────────────────────────────────────────
# IsAlgo — Translation Management
# ──────────────────────────────────────────────
# Run `make help-translations` to see all available commands.
# ──────────────────────────────────────────────

PYTHON ?= ./venv_etv/bin/python
MANAGE = $(PYTHON) manage.py

# Languages matching settings.LANGUAGES (exclude 'en' — it's the source)
LANGS = fr es de zh_Hans ja ar ru

# Folders to ignore (not user-facing / no translatable strings)
IGNORE_DIRS = \
	--ignore="__strategies__/*" \
	--ignore="venv_etv/*" \
	--ignore="node_modules/*" \
	--ignore="static/*" \
	--ignore="vector_index/*" \
	--ignore="tero_app/*" \
	--ignore="ctrader_bridge/*" \
	--ignore="aws_task_definitions/*" \
	--ignore=".git/*" \
	--ignore=".github/*" \
	--ignore=".pytest_cache/*" \
	--ignore="__pycache__/*" \
	--ignore="*.pyc" \
	--ignore="migrations/*"

# ── Extract messages for ALL languages ──
.PHONY: messages
messages:
	@echo "📦 Extracting translatable strings..."
	@for lang in $(LANGS); do \
		echo "  → $$lang"; \
		$(MANAGE) makemessages -l $$lang $(IGNORE_DIRS) --no-location; \
	done
	@echo "✅ Done. Edit .po files in locale/*/LC_MESSAGES/django.po"

# ── Extract messages for a SINGLE language ──
#    Usage: make messages-fr, make messages-es, etc.
.PHONY: $(addprefix messages-,$(LANGS))
$(addprefix messages-,$(LANGS)):
	@lang=$(@:messages-%=%); \
	echo "📦 Extracting strings for $$lang..."; \
	$(MANAGE) makemessages -l $$lang $(IGNORE_DIRS) --no-location; \
	echo "✅ Done. Edit locale/$$lang/LC_MESSAGES/django.po"

# ── Compile .po → .mo ──
.PHONY: compile
compile:
	@echo "⚙️  Compiling translations..."
	$(MANAGE) compilemessages --ignore="venv_etv/*"
	@echo "✅ Compiled .mo files ready."

# ── Extract + compile in one step ──
.PHONY: translations
translations: messages compile

# ── Remove compiled .mo files ──
.PHONY: clean-messages
clean-messages:
	@echo "🗑  Removing compiled .mo files..."
	find locale -name "*.mo" -delete 2>/dev/null || true
	@echo "✅ Cleaned."

# ── Show translation stats ──
.PHONY: stats
stats:
	@echo "📊 Translation statistics:"
	@for lang in $(LANGS); do \
		po="locale/$$lang/LC_MESSAGES/django.po"; \
		if [ -f "$$po" ]; then \
			$(PYTHON) -c "import polib,sys; po=polib.pofile(sys.argv[1]); total=len([e for e in po if e.msgid]); untrans=len(po.untranslated_entries()); print(f'  {sys.argv[2]}: {total-untrans} / {total} translated')" "$$po" "$$lang"; \
		else \
			echo "  $$lang: no .po file (run 'make messages' first)"; \
		fi \
	done

# ── Show untranslated messages with line numbers ──
.PHONY: missing
missing:
	@for lang in $(LANGS); do \
		po="locale/$$lang/LC_MESSAGES/django.po"; \
		if [ -f "$$po" ]; then \
			$(PYTHON) -c "import polib,sys; po=polib.pofile(sys.argv[1]); entries=po.untranslated_entries(); print(f'  {sys.argv[2]}: all translated') if not entries else [print(f'=== {sys.argv[2]} ({len(entries)} untranslated) ===')] + [print(f'  Line {e.linenum}: {e.msgid[:120]}') for e in entries]" "$$po" "$$lang"; \
		else \
			echo "  $$lang: no .po file (run 'make messages' first)"; \
		fi \
	done

# ── Show fuzzy (auto-suggested, needs review) entries ──
.PHONY: fuzzy
fuzzy:
	@echo "🔍 Fuzzy entries (need review):"
	@for lang in $(LANGS); do \
		po="locale/$$lang/LC_MESSAGES/django.po"; \
		if [ -f "$$po" ]; then \
			$(PYTHON) -c "import polib,sys; po=polib.pofile(sys.argv[1]); entries=po.fuzzy_entries(); print(f'  {sys.argv[2]}: no fuzzy entries') if not entries else [print(f'=== {sys.argv[2]} ({len(entries)} fuzzy) ===')] + [print(f'  Line {e.linenum}: {e.msgid[:120]}') for e in entries]" "$$po" "$$lang"; \
		else \
			echo "  $$lang: no .po file"; \
		fi \
	done

# ── Validate PO file syntax ──
.PHONY: validate
validate:
	@echo "🔎 Validating PO files..."
	@errors=0; \
	for lang in $(LANGS); do \
		po="locale/$$lang/LC_MESSAGES/django.po"; \
		if [ -f "$$po" ]; then \
			if msgfmt --check-format --check-domain -o /dev/null "$$po" 2>/dev/null; then \
				echo "  $$lang: ✅ valid"; \
			else \
				echo "  $$lang: ❌ errors found"; \
				msgfmt --check-format --check-domain -o /dev/null "$$po" 2>&1 | head -20; \
				errors=1; \
			fi \
		else \
			echo "  $$lang: no .po file"; \
		fi \
	done; \
	if [ "$$errors" = "1" ]; then echo "⚠️  Some files have errors."; exit 1; fi; \
	echo "✅ All PO files are valid."

# ── Export untranslated msgids to JSON ──
#    Usage: make export-missing lang=fr
.PHONY: export-missing
export-missing:
	@if [ -z "$(lang)" ]; then \
		echo "Usage: make export-missing lang=<lang>"; \
		echo "  Exports untranslated msgids to locale/<lang>_missing.json"; \
		echo "  Available: $(LANGS)"; \
		exit 1; \
	fi
	$(PYTHON) locale/manage_translations.py export $(lang)

# ── Fill translations from a JSON file ──
#    Usage: make fill lang=fr file=locale/fr_missing.json
.PHONY: fill
fill:
	@if [ -z "$(lang)" ] || [ -z "$(file)" ]; then \
		echo "Usage: make fill lang=<lang> file=<translations.json>"; \
		echo "  JSON format: { \"source text\": \"translated text\", ... }"; \
		exit 1; \
	fi
	$(PYTHON) locale/manage_translations.py fill $(lang) $(file)

# ── Export fuzzy entries to JSON ──
#    Usage: make export-fuzzy lang=fr
.PHONY: export-fuzzy
export-fuzzy:
	@if [ -z "$(lang)" ]; then \
		echo "Usage: make export-fuzzy lang=<lang>"; \
		echo "  Exports fuzzy msgids (with current msgstr) to locale/<lang>_fuzzy.json"; \
		echo "  Available: $(LANGS)"; \
		exit 1; \
	fi
	$(PYTHON) locale/manage_translations.py export-fuzzy $(lang)

# ── Fix fuzzy entries from a JSON file ──
#    Usage: make fix-fuzzy lang=fr file=locale/fr_fuzzy.json
.PHONY: fix-fuzzy
fix-fuzzy:
	@if [ -z "$(lang)" ] || [ -z "$(file)" ]; then \
		echo "Usage: make fix-fuzzy lang=<lang> file=<translations.json>"; \
		echo "  JSON format: { \"source text\": \"corrected translation\", ... }"; \
		exit 1; \
	fi
	$(PYTHON) locale/manage_translations.py fix-fuzzy $(lang) $(file)

# ── Full overview: stats + missing + fuzzy ──
.PHONY: overview
overview: stats
	@echo ""
	@$(MAKE) --no-print-directory missing
	@echo ""
	@$(MAKE) --no-print-directory fuzzy

# ── Show all available translation commands ──
.PHONY: help-translations
help-translations:
	@echo "Translation commands:"
	@echo "  make messages          — Extract translatable strings for all languages"
	@echo "  make messages-<lang>   — Extract for one language (e.g. make messages-fr)"
	@echo "  make compile           — Compile .po → .mo files"
	@echo "  make translations      — Extract + compile in one step"
	@echo "  make clean-messages    — Remove all compiled .mo files"
	@echo "  make stats             — Show translated/total counts per language"
	@echo "  make missing           — Show untranslated entries with line numbers"
	@echo "  make fuzzy             — Show fuzzy entries that need review"
	@echo "  make validate          — Validate PO file syntax with msgfmt"
	@echo "  make overview          — Full report: stats + missing + fuzzy"
	@echo "  make export-missing lang=<lang> — Export untranslated msgids to JSON"
	@echo "  make fill lang=<lang> file=<json> — Fill translations from a JSON file"
	@echo "  make export-fuzzy lang=<lang>     — Export fuzzy msgids to JSON"
	@echo "  make fix-fuzzy lang=<lang> file=<json> — Fix fuzzy entries from a JSON file"
	@echo "  make help-translations — Show this help"

# ──────────────────────────────────────────────
# IsAlgo — Translation Management
# ──────────────────────────────────────────────
# Usage:
#   make messages        — Extract translatable strings for all languages
#   make messages-fr     — Extract for French only
#   make compile         — Compile .po → .mo files
#   make translations    — Extract + compile in one step
#   make clean-messages  — Remove all compiled .mo files
#   make missing         — Show untranslated messages with line numbers
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
			total=$$(awk '/^msgid "/ && $$0 != "msgid \"\"" {c++} END {print c+0}' "$$po"); \
			empty=$$(awk 'BEGIN{m=0;e=0} /^msgid "/ {m=($$0 != "msgid \"\"")} m && /^msgstr ""$$/ {e++} END {print e+0}' "$$po"); \
			translated=$$((total - empty)); \
			echo "  $$lang: $$translated / $$total translated"; \
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

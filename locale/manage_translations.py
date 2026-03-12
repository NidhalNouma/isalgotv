#!/usr/bin/env python3
"""
Manage translations: export/fill missing entries and export/fix fuzzy entries.

Usage:
    Export missing:  python locale/manage_translations.py export <lang>
                     → writes locale/<lang>_missing.json

    Fill from JSON:  python locale/manage_translations.py fill <lang> <translations.json>
                     → fills empty msgstr entries in the PO file

    Export fuzzy:    python locale/manage_translations.py export-fuzzy <lang>
                     → writes locale/<lang>_fuzzy.json  (msgid → current wrong msgstr)

    Fix fuzzy:       python locale/manage_translations.py fix-fuzzy <lang> <translations.json>
                     → replaces msgstr for fuzzy entries and removes the fuzzy flag
"""
import json
import os
import re
import sys

LOCALE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(LOCALE_DIR)


def po_path_for(lang):
    return os.path.join(LOCALE_DIR, lang, "LC_MESSAGES", "django.po")


# ── PO helpers ──────────────────────────────────────────


def unescape_po(s):
    return s.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")


def escape_po(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


# ── Export ──────────────────────────────────────────────


def export_missing(lang):
    """Write a JSON file containing all untranslated msgids for *lang*."""
    try:
        import polib
    except ImportError:
        sys.exit("polib is required.  pip install polib")

    path = po_path_for(lang)
    if not os.path.isfile(path):
        sys.exit(f"PO file not found: {path}")

    po = polib.pofile(path)
    missing = {e.msgid: "" for e in po.untranslated_entries()}

    if not missing:
        print(f"{lang}: all entries are translated — nothing to export.")
        return

    out = os.path.join(LOCALE_DIR, f"{lang}_missing.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(missing, f, ensure_ascii=False, indent=2)

    print(f"{lang}: exported {len(missing)} untranslated msgids → {out}")
    print(f"Fill in the empty values, then run:")
    print(f"  make fill lang={lang} file={out}")


# ── Fill ────────────────────────────────────────────────


def fill_po(lang, translations):
    """Fill empty msgstr entries in the PO file using *translations* dict."""
    path = po_path_for(lang)
    if not os.path.isfile(path):
        sys.exit(f"PO file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().split("\n")

    result = []
    i = 0
    filled = 0
    skipped = 0

    while i < len(lines):
        line = lines[i]

        # Detect msgid (skip msgid_plural)
        if line.startswith('msgid "') and not line.startswith("msgid_plural"):
            msgid_lines = [line]
            i += 1
            while i < len(lines) and lines[i].startswith('"'):
                msgid_lines.append(lines[i])
                i += 1

            # Parse msgid string
            first = re.match(r'^msgid "(.*)"$', msgid_lines[0])
            if first:
                parts = [first.group(1)] + [
                    re.match(r'^"(.*)"$', l).group(1)
                    for l in msgid_lines[1:]
                    if re.match(r'^"(.*)"$', l)
                ]
                msgid_str = unescape_po("".join(parts))
            else:
                result.extend(msgid_lines)
                continue

            result.extend(msgid_lines)

            # Now expect msgstr
            if i < len(lines) and lines[i].startswith('msgstr "'):
                msgstr_lines = [lines[i]]
                i += 1
                while i < len(lines) and lines[i].startswith('"'):
                    msgstr_lines.append(lines[i])
                    i += 1

                first_ms = re.match(r'^msgstr "(.*)"$', msgstr_lines[0])
                if first_ms:
                    ms_parts = [first_ms.group(1)] + [
                        re.match(r'^"(.*)"$', l).group(1)
                        for l in msgstr_lines[1:]
                        if re.match(r'^"(.*)"$', l)
                    ]
                    msgstr_str = "".join(ms_parts)

                    if (
                        msgstr_str == ""
                        and msgid_str != ""
                        and msgid_str in translations
                        and translations[msgid_str]  # non-empty value
                    ):
                        escaped = escape_po(translations[msgid_str])
                        if len(escaped) > 75:
                            result.append('msgstr ""')
                            while escaped:
                                result.append(f'"{escaped[:75]}"')
                                escaped = escaped[75:]
                        else:
                            result.append(f'msgstr "{escaped}"')
                        filled += 1
                    elif msgstr_str == "" and msgid_str != "" and msgid_str not in translations:
                        skipped += 1
                        result.extend(msgstr_lines)
                    else:
                        result.extend(msgstr_lines)
                else:
                    result.extend(msgstr_lines)
            continue

        result.append(line)
        i += 1

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(result))

    print(f"{lang}: filled {filled} entries")
    if skipped:
        print(f"  {skipped} entries still empty (no translation provided in JSON)")


# ── Export fuzzy ────────────────────────────────────────


def export_fuzzy(lang):
    """Write a JSON file containing all fuzzy msgids with their current (wrong) msgstr."""
    try:
        import polib
    except ImportError:
        sys.exit("polib is required.  pip install polib")

    path = po_path_for(lang)
    if not os.path.isfile(path):
        sys.exit(f"PO file not found: {path}")

    po = polib.pofile(path)
    fuzzy = {e.msgid: e.msgstr for e in po.fuzzy_entries()}

    if not fuzzy:
        print(f"{lang}: no fuzzy entries — nothing to export.")
        return

    out = os.path.join(LOCALE_DIR, f"{lang}_fuzzy.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(fuzzy, f, ensure_ascii=False, indent=2)

    print(f"{lang}: exported {len(fuzzy)} fuzzy msgids → {out}")
    print(f"Review/fix the translations, then run:")
    print(f"  make fix-fuzzy lang={lang} file={out}")


# ── Fix fuzzy ───────────────────────────────────────────


def fix_fuzzy(lang, translations):
    """Replace msgstr for fuzzy entries using *translations* dict and remove the fuzzy flag."""
    try:
        import polib
    except ImportError:
        sys.exit("polib is required.  pip install polib")

    path = po_path_for(lang)
    if not os.path.isfile(path):
        sys.exit(f"PO file not found: {path}")

    po = polib.pofile(path)
    fixed = 0
    skipped = 0

    for entry in po.fuzzy_entries():
        if entry.msgid in translations and translations[entry.msgid]:
            entry.msgstr = translations[entry.msgid]
            entry.flags.remove("fuzzy")
            fixed += 1
        else:
            skipped += 1

    po.save(path)
    print(f"{lang}: fixed {fixed} fuzzy entries")
    if skipped:
        print(f"  {skipped} fuzzy entries unchanged (no translation provided in JSON)")


# ── CLI ──────────────────────────────────────────────────


def main():
    if len(sys.argv) < 3:
        print(__doc__.strip())
        sys.exit(1)

    cmd = sys.argv[1]
    lang = sys.argv[2]

    if cmd == "export":
        export_missing(lang)
    elif cmd == "fill":
        if len(sys.argv) < 4:
            sys.exit("Usage: manage_translations.py fill <lang> <translations.json>")
        with open(sys.argv[3], "r", encoding="utf-8") as f:
            translations = json.load(f)
        if not isinstance(translations, dict):
            sys.exit("JSON file must contain a flat object { \"msgid\": \"translation\", ... }")
        fill_po(lang, translations)
    elif cmd == "export-fuzzy":
        export_fuzzy(lang)
    elif cmd == "fix-fuzzy":
        if len(sys.argv) < 4:
            sys.exit("Usage: manage_translations.py fix-fuzzy <lang> <translations.json>")
        with open(sys.argv[3], "r", encoding="utf-8") as f:
            translations = json.load(f)
        if not isinstance(translations, dict):
            sys.exit("JSON file must contain a flat object { \"msgid\": \"translation\", ... }")
        fix_fuzzy(lang, translations)
    else:
        sys.exit(f"Unknown command: {cmd}. Use 'export', 'fill', 'export-fuzzy', or 'fix-fuzzy'.")


if __name__ == "__main__":
    main()

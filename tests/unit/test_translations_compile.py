# Calibre-Web Automated – fork of Calibre-Web
# Copyright (C) 2018-2026 Calibre-Web contributors
# Copyright (C) 2024-2026 Calibre-Web Automated contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# See CONTRIBUTORS for full list of authors.

"""The translation catalogs have to compile, or the image ships without that language."""

from collections import Counter
from pathlib import Path
import shutil
import subprocess

import polib
import pytest

TRANSLATIONS = Path(__file__).resolve().parents[2] / "cps" / "translations"
CATALOGS = sorted(TRANSLATIONS.glob("*/LC_MESSAGES/messages.po"))


@pytest.mark.unit
class TestTranslationCatalogs:
    def test_only_spanish_is_shipped(self):
        assert [p.parts[-3] for p in CATALOGS] == ["es"]

    @pytest.mark.parametrize("catalog", CATALOGS, ids=lambda p: p.parts[-3])
    def test_no_duplicate_message(self, catalog):
        # msgfmt rejects a msgid defined twice, and it counts obsolete (#~) entries too
        # Iterating the catalog yields the obsolete entries along with the active ones
        counts = Counter((entry.msgctxt, entry.msgid) for entry in polib.pofile(str(catalog)))
        assert [key for key, count in counts.items() if count > 1] == []

    @pytest.mark.parametrize("catalog", CATALOGS, ids=lambda p: p.parts[-3])
    def test_placeholders_survive_translation(self, catalog):
        import re
        placeholder = re.compile(r"%\([a-z_]+\)[sd]")
        broken = [entry.msgid for entry in polib.pofile(str(catalog)).translated_entries()
                  if sorted(placeholder.findall(entry.msgid)) != sorted(placeholder.findall(entry.msgstr))]
        assert broken == []

    @pytest.mark.skipif(shutil.which("msgfmt") is None, reason="gettext is not installed")
    @pytest.mark.parametrize("catalog", CATALOGS, ids=lambda p: p.parts[-3])
    def test_msgfmt_compiles_it(self, catalog, tmp_path):
        result = subprocess.run(["msgfmt", "--check", str(catalog), "-o", str(tmp_path / "messages.mo")],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr

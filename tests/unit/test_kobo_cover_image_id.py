# Calibre-Web Automated – fork of Calibre-Web
# Copyright (C) 2018-2026 Calibre-Web contributors
# Copyright (C) 2024-2026 Calibre-Web Automated contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# See CONTRIBUTORS for full list of authors.

"""Unit tests for Kobo cover cache-busting helpers."""

from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path
import uuid as uuidlib

import pytest


def _load_cover_cache_module():
    module_path = Path(__file__).resolve().parents[2] / "cps" / "kobo_cover_cache.py"
    spec = importlib.util.spec_from_file_location("kobo_cover_cache", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kobo_cache = _load_cover_cache_module()


@pytest.mark.unit
class TestKoboCoverImageId:
    def test_normalize_cover_uuid_keeps_plain_uuid(self):
        value = str(uuidlib.uuid4())
        assert kobo_cache.normalize_cover_uuid(value) == value

    def test_normalize_cover_uuid_strips_numeric_suffix(self):
        base = str(uuidlib.uuid4())
        value = f"{base}-1700000000"
        assert kobo_cache.normalize_cover_uuid(value) == base

    def test_normalize_cover_uuid_ignores_non_numeric_suffix(self):
        base = str(uuidlib.uuid4())
        value = f"{base}-notanumber"
        assert kobo_cache.normalize_cover_uuid(value) == value

    def test_cover_image_id_uses_mtime_when_local_cover_exists(self, tmp_path):
        book_uuid = uuidlib.uuid4()
        cover_dir = tmp_path / "Author" / "Title"
        cover_dir.mkdir(parents=True, exist_ok=True)
        cover_file = cover_dir / "cover.jpg"
        cover_file.write_bytes(b"test")

        mtime = 1700000123
        os.utime(cover_file, (mtime, mtime))

        expected = f"{book_uuid}-{mtime}"
        assert kobo_cache.build_cover_image_id(
            str(book_uuid),
            use_google_drive=False,
            last_modified=None,
            cover_path=str(cover_file),
        ) == expected

    def test_cover_image_id_falls_back_without_cover(self, tmp_path):
        book_uuid = uuidlib.uuid4()
        cover_path = tmp_path / "Missing" / "Cover" / "cover.jpg"
        assert kobo_cache.build_cover_image_id(
            str(book_uuid),
            use_google_drive=False,
            last_modified=None,
            cover_path=str(cover_path),
        ) == str(book_uuid)

    def test_cover_image_id_uses_last_modified_on_gdrive(self):
        book_uuid = uuidlib.uuid4()
        last_modified = datetime(2026, 2, 5, 12, 30, 0, tzinfo=timezone.utc)
        expected = f"{book_uuid}-{int(last_modified.timestamp())}"
        assert kobo_cache.build_cover_image_id(
            str(book_uuid),
            use_google_drive=True,
            last_modified=last_modified,
            cover_path=None,
        ) == expected


@pytest.mark.unit
class TestKoboCoverChangedSince:
    """A Kobo ignores a new CoverImageId in a ChangedEntitlement, so sync needs to know
    whether the cover was replaced after the device's last sync."""

    def _cover(self, tmp_path, mtime):
        cover_file = tmp_path / "cover.jpg"
        cover_file.write_bytes(b"test")
        os.utime(cover_file, (mtime, mtime))
        return str(cover_file)

    def test_cover_newer_than_last_sync(self, tmp_path):
        cover = self._cover(tmp_path, datetime(2026, 10, 9, 11, 51, 5, tzinfo=timezone.utc).timestamp())
        assert kobo_cache.cover_changed_since(cover, datetime(2026, 10, 9, 11, 50, 19)) is True

    def test_cover_older_than_last_sync(self, tmp_path):
        cover = self._cover(tmp_path, datetime(2026, 9, 26, 12, 42, 27, tzinfo=timezone.utc).timestamp())
        assert kobo_cache.cover_changed_since(cover, datetime(2026, 10, 9, 11, 50, 19)) is False

    def test_since_is_compared_as_utc(self, tmp_path):
        # Sync token timestamps are naive UTC; a local-time comparison would be off by the UTC offset
        cover = self._cover(tmp_path, datetime(2026, 10, 9, 12, 0, 0, tzinfo=timezone.utc).timestamp())
        assert kobo_cache.cover_changed_since(cover, datetime(2026, 10, 9, 11, 59, 0)) is True
        assert kobo_cache.cover_changed_since(cover, datetime(2026, 10, 9, 12, 1, 0)) is False

    def test_missing_cover(self, tmp_path):
        assert kobo_cache.cover_changed_since(str(tmp_path / "cover.jpg"), datetime(2026, 1, 1)) is False

    def test_no_cover_path(self):
        assert kobo_cache.cover_changed_since(None, datetime(2026, 1, 1)) is False

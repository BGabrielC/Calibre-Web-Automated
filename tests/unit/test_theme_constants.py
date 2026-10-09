# Calibre-Web Automated – fork of Calibre-Web
# Copyright (C) 2018-2026 Calibre-Web contributors
# Copyright (C) 2024-2026 Calibre-Web Automated contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# See CONTRIBUTORS for full list of authors.

"""Unit tests for theme value validation."""

import pytest

from cps import constants


@pytest.mark.unit
class TestThemeOrDefault:
    @pytest.mark.parametrize("value", [constants.THEME_CALIBLUR, constants.THEME_F1, "1", "2"])
    def test_valid_theme_is_kept(self, value):
        assert constants.theme_or_default(value) == int(value)

    @pytest.mark.parametrize("value", [0, "0", 3, "", "dark", None])
    def test_invalid_theme_falls_back_to_default(self, value):
        assert constants.theme_or_default(value) == constants.DEFAULT_THEME

    def test_default_theme_is_f1(self):
        assert constants.DEFAULT_THEME == constants.THEME_F1

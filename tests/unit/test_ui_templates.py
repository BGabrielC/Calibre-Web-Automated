# Calibre-Web Automated – fork of Calibre-Web
# Copyright (C) 2018-2026 Calibre-Web contributors
# Copyright (C) 2024-2026 Calibre-Web Automated contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# See CONTRIBUTORS for full list of authors.

"""Unit tests for the template lookup that lets redesigned pages replace legacy ones."""

import importlib.util
from pathlib import Path

from jinja2 import DictLoader, Environment, TemplateNotFound
import pytest


def _load_ui_templates_module():
    module_path = Path(__file__).resolve().parents[2] / "cps" / "ui_templates.py"
    spec = importlib.util.spec_from_file_location("ui_templates", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ui_templates = _load_ui_templates_module()

LEGACY = DictLoader({
    "layout.html": "legacy layout[{% block body %}{% endblock %}]",
    "index.html": '{% extends "layout.html" %}{% block body %}legacy index{% endblock %}',
    "detail.html": '{% extends "layout.html" %}{% block body %}legacy detail{% endblock %}',
})
REDESIGNED = DictLoader({
    "layout.html": "new layout[{% block body %}{% endblock %}]",
    "index.html": '{% extends "layout.html" %}{% block body %}new index{% endblock %}',
    "wrapped.html": 'wrapping {% include "legacy/detail.html" %}',
})


def _render(name, force_legacy=False):
    loader = ui_templates.build_template_loader(LEGACY, REDESIGNED, force_legacy=force_legacy)
    return Environment(loader=loader).get_template(name).render()


@pytest.mark.unit
class TestTemplateLookup:
    def test_redesigned_page_replaces_legacy_one(self):
        assert _render("index.html") == "new layout[new index]"

    def test_page_without_redesign_falls_back_to_legacy(self):
        # A legacy page extends "layout.html", so it is hosted inside the redesigned frame
        assert _render("detail.html") == "new layout[legacy detail]"

    def test_legacy_prefix_reaches_the_original_template(self):
        assert _render("legacy/layout.html") == "legacy layout[]"
        assert _render("wrapped.html") == "wrapping new layout[legacy detail]"

    def test_forcing_legacy_ignores_redesigned_pages(self):
        assert _render("index.html", force_legacy=True) == "legacy layout[legacy index]"
        with pytest.raises(TemplateNotFound):
            _render("wrapped.html", force_legacy=True)

    def test_unknown_template_is_not_found(self):
        with pytest.raises(TemplateNotFound):
            _render("missing.html")


@pytest.mark.unit
class TestLegacyUiForced:
    @pytest.mark.parametrize("value", ["legacy", "LEGACY", " legacy "])
    def test_legacy_value_forces_legacy(self, value):
        assert ui_templates.legacy_ui_forced({"CWA_UI": value}) is True

    @pytest.mark.parametrize("environ", [{}, {"CWA_UI": ""}, {"CWA_UI": "hig"}])
    def test_anything_else_keeps_redesign(self, environ):
        assert ui_templates.legacy_ui_forced(environ) is False

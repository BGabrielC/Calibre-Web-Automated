# -*- coding: utf-8 -*-
# Calibre-Web Automated – fork of Calibre-Web
# Copyright (C) 2018-2026 Calibre-Web contributors
# Copyright (C) 2024-2026 Calibre-Web Automated contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# See CONTRIBUTORS for full list of authors.

"""Template lookup for the redesigned interface.

Redesigned pages live in templates/hig/ under the same name as the legacy page they replace,
so a page is switched over by adding its template there. These helpers are dependency-light
so they can be tested without importing the full application package.
"""

import os

from jinja2 import ChoiceLoader, PrefixLoader

HIG_TEMPLATE_DIR = "hig"
LEGACY_PREFIX = "legacy"


def legacy_ui_forced(environ=None):
    """Whether CWA_UI=legacy asks for the legacy interface, as an escape hatch."""
    environ = os.environ if environ is None else environ
    return environ.get("CWA_UI", "").strip().lower() == "legacy"


def build_template_loader(legacy_loader, redesigned_loader, force_legacy=False):
    """Look templates up in the redesigned set first and fall back to the legacy one.

    "legacy/<name>" always reaches the legacy template, for redesigned pages that wrap one.
    """
    if force_legacy:
        return legacy_loader
    return ChoiceLoader([redesigned_loader, legacy_loader, PrefixLoader({LEGACY_PREFIX: legacy_loader})])

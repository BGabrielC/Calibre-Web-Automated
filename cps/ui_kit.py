# -*- coding: utf-8 -*-
# Calibre-Web Automated – fork of Calibre-Web
# Copyright (C) 2018-2026 Calibre-Web contributors
# Copyright (C) 2024-2026 Calibre-Web Automated contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# See CONTRIBUTORS for full list of authors.

"""Component gallery of the redesigned interface, for checking the design system in one place."""

from flask import Blueprint, render_template

from .admin import admin_required
from .usermanagement import user_login_required

ui_kit = Blueprint('ui_kit', __name__)


@ui_kit.route("/hig-kit")
@user_login_required
@admin_required
def kit():
    return render_template('hig/kit.html')

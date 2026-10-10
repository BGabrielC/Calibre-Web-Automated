# Redesigned templates

A template placed here replaces the legacy template of the same name in `cps/templates/`
(see `cps/ui_templates.py`). The legacy version stays reachable as `legacy/<name>`, for
example `{% extends "legacy/layout.html" %}`.

Static files for these pages go in `cps/static/hig/`. Setting the environment variable
`CWA_UI=legacy` ignores this folder and serves the legacy interface.

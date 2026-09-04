"""Single source of truth for the PrusaToOrca version.

Read by app.py, by tools/make_version_info.py (PE metadata) and by the
release workflow, which checks that the git tag matches this value.
"""

__version__ = "1.1.1"

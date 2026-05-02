"""Bounded RFO runtime package (v19+).

Implementation lives in ``runtime/*_impl.py`` modules and ``runtime/cli.py`` (argparse
entry). ``runtime/impl.py`` remains a **deprecated** compatibility shim that re-exports
``main``, ``validate``, and ``cmd_*`` callables for older import paths — prefer importing
from ``runtime.cli`` or the specific ``*_impl`` module.
"""

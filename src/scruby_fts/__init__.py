# Manticore Search is an open-source database that was created in 2017 as
# a continuation of the Sphinx Search engine.
# We built upon its strengths, significantly improving its functionality and
# fixing hundreds of bugs while keeping it open-source.
# This has made Manticore Search a modern, fast, lightweight,
# and fully-featured database with outstanding full-text search capabilities.
#
# Manticore Search is distributed under GPLv3 or later.
# Manticore Search uses and re-distributes other open-source components.
# Please check the component licenses directory for details:
# https://github.com/manticoresoftware/manticoresearch/blob/master/component-licenses
#
#
# Copyright (c) 2026 Gennady Kostyunin
# SPDX-License-Identifier: MIT
# SPDX-License-Identifier: GPL-3.0-or-later
"""Scruby-FTS - Full-text search with Manticore Search."""

from __future__ import annotations

__all__ = (
    "FullTextSearch",
    "FTSConfig",
)

from scruby_fts.config import FTSConfig
from scruby_fts.plugin import FullTextSearch

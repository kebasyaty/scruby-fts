# Scruby-FTS - Full-text search with Manticore Search.
# Copyright (c) 2026 Gennady Kostyunin
# SPDX-License-Identifier: MIT
# SPDX-License-Identifier: GPL-3.0-or-later
#
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
"""Plugin settings.

The settings class contains the following parameters:

- `config` - Configuration options for https://github.com/manticoresoftware/manticoresearch-python-asyncio.
- `languages` - List of supported languages and full-text search algorithms.
"""

from __future__ import annotations

__all__ = ("FTSConfig",)

from typing import ClassVar, final

from manticoresearch.configuration import Configuration
from xloft import AliasDict


@final
class FTSConfig:
    """FullTextSearch plugin settings."""

    config: ClassVar[Configuration] = Configuration(host="http://127.0.0.1:9312")

    # List of supported languages for full-text search.
    morphology: ClassVar[AliasDict] = AliasDict(
        ({"Arabic", "ar"}, "libstemmer_ar"),
        ({"Catalan", "ca"}, "libstemmer_ca"),
        ({"Chinese", "zh"}, "jieba_chinese"),
        ({"Czech", "cz"}, "stem_cz"),
        ({"Danish", "da"}, "libstemmer_da"),
        ({"Dutch", "hl"}, "libstemmer_nl"),
        ({"English", "en"}, "lemmatize_en_all"),
        ({"Finnish", "fi"}, "libstemmer_fi"),
        ({"French", "fr"}, "libstemmer_fr"),
        ({"German", "de"}, "lemmatize_de_all"),
        ({"Greek", "el"}, "libstemmer_el"),
        ({"Hindi", "hi"}, "libstemmer_hi"),
        ({"Hungarian", "hu"}, "libstemmer_hu"),
        ({"Indonesian", "id"}, "libstemmer_id"),
        ({"Irish", "ga"}, "libstemmer_ga"),
        ({"Italian", "it"}, "libstemmer_it"),
        ({"Japanese", "ja"}, "ngram_chars=japanese ngram_len=1"),
        ({"Korean", "ko"}, "ngram_chars=korean ngram_len=1"),
        ({"Lithuanian", "lt"}, "libstemmer_lt"),
        ({"Nepali", "ne"}, "libstemmer_ne"),
        ({"Norwegian", "no"}, "libstemmer_no"),
        ({"Portuguese", "pt"}, "libstemmer_pt"),
        ({"Romanian", "ro"}, "libstemmer_ro"),
        ({"Russian", "ru"}, "lemmatize_ru_all"),
        ({"Spanish", "es"}, "libstemmer_es"),
        ({"Swedish", "sv"}, "libstemmer_sv"),
        ({"Tamil", "ta"}, "libstemmer_ta"),
        ({"Turkish", "tr"}, "libstemmer_tr"),
    )

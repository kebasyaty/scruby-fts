"""Test a settings module."""

from __future__ import annotations

from xloft import AliasDict

from scruby_fts import FTSConfig

TEST_MORPHOLOGY = AliasDict(
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


class TestPositive:
    """Positive tests."""

    def test_supported_languages(self) -> None:
        """Test supported languages."""
        for lang, morphology in TEST_MORPHOLOGY.items():
            morphology_by_lang_name = FTSConfig.morphology.get(lang[0])
            morphology_by_lang_code = FTSConfig.morphology.get(lang[1])
            assert morphology_by_lang_name == morphology
            assert morphology_by_lang_code == morphology

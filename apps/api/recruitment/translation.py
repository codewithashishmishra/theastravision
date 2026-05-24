"""Offline Hindi (and other) to English via Argos Translate."""

from __future__ import annotations

_translator = None


def _get_hi_en_translator():
    global _translator
    if _translator is not None:
        return _translator
    try:
        import argostranslate.package
        import argostranslate.translate

        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()
        pkg = next(
            (p for p in available if p.from_code == 'hi' and p.to_code == 'en'),
            None,
        )
        if pkg and not pkg.is_installed():
            argostranslate.package.install_from_path(pkg.download())
        _translator = argostranslate.translate.get_translation_from_codes('hi', 'en')
        return _translator
    except Exception:
        return None


def to_english(text: str, source_lang: str = '') -> str:
    if not text or not text.strip():
        return ''
    lang = (source_lang or '').lower()
    if lang.startswith('en') or lang == 'english':
        return text.strip()
    if lang.startswith('hi') or lang in ('hin', 'hindi'):
        translator = _get_hi_en_translator()
        if translator:
            try:
                return translator.translate(text.strip())
            except Exception:
                pass
    # Fallback: return original if no translator
    return text.strip()

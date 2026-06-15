"""Вспомогательные утилиты приложения users.

Содержит:
- константы для валидации профиля (телефон, GitHub-ссылка);
- функции-валидаторы (используются формами users и projects);
- генератор автоматических аватарок (PNG с буквой имени).
"""
import io
import random
import re
from urllib.parse import urlparse

from django import forms
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

# === Валидация телефона =====================================================

# Сколько цифр идёт после префикса (8 или +7).
PHONE_DIGITS_AFTER_PREFIX = 10
# Полная длина телефона в формате 8XXXXXXXXXX (8 + 10 цифр).
PHONE_FULL_LENGTH_8_PREFIX = 11
# Регулярка для уже нормализованного телефона: 8XXX… или +7XXX….
PHONE_RE = re.compile(rf"^(?:8|\+7)\d{{{PHONE_DIGITS_AFTER_PREFIX}}}$")
# Префиксы, которые приводим к +7.
PHONE_LEADING_8 = "8"
PHONE_NORMALIZED_PREFIX = "+7"
# Текстовые сообщения об ошибках валидации профиля.
PHONE_FORMAT_ERROR = (
    "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX"
)
PHONE_DUPLICATE_ERROR = "Этот номер телефона уже используется"

# === Валидация GitHub-ссылки ================================================

ALLOWED_GITHUB_HOST = "github.com"
ALLOWED_URL_SCHEMES = ("http", "https")
INVALID_URL_ERROR = "Некорректная ссылка"
NON_GITHUB_URL_ERROR = "Ссылка должна вести на github.com"

# === Параметры аватаров =====================================================

# Палитра приглушённых тёмных цветов: на них хорошо читается белая буква.
AVATAR_PALETTE = (
    "#1f6feb", "#388bfd", "#0969da", "#1a7f37", "#2da44e",
    "#9a6700", "#bc4c00", "#8250df", "#a475f9", "#cf222e",
    "#d1242f", "#0a3069", "#116329", "#7d4e00", "#82071e",
)
AVATAR_SIZE = 256
AVATAR_FONT_SIZE_RATIO = 0.55
AVATAR_TEXT_COLOR = "#ffffff"
AVATAR_FALLBACK_LETTER = "?"
AVATAR_IMAGE_FORMAT = "PNG"

FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
)


# === Функции-валидаторы =====================================================


def normalize_phone(raw: str) -> str:
    """Привести телефон к формату ``+7XXXXXXXXXX``.

    Пустая строка возвращается как есть. Используется в форме редактирования
    профиля и косвенно в проверке уникальности номера.
    """
    raw = (raw or "").strip().replace(" ", "").replace("-", "")
    if not raw:
        return ""
    if raw.startswith(PHONE_LEADING_8) and len(raw) == PHONE_FULL_LENGTH_8_PREFIX:
        return PHONE_NORMALIZED_PREFIX + raw[1:]
    return raw


def validate_github_url(value: str) -> str:
    """Проверить, что ссылка валидная и ведёт на ``github.com``.

    Используется и формой профиля пользователя, и формой проекта.
    """
    if not value:
        return value
    parsed = urlparse(value)
    if parsed.scheme not in ALLOWED_URL_SCHEMES or not parsed.netloc:
        raise forms.ValidationError(INVALID_URL_ERROR)
    host = parsed.netloc.lower()
    if host != ALLOWED_GITHUB_HOST and not host.endswith("." + ALLOWED_GITHUB_HOST):
        raise forms.ValidationError(NON_GITHUB_URL_ERROR)
    return value


# === Генерация аватара ======================================================


def generate_avatar(letter: str, *, seed: str | None = None) -> ContentFile:
    """Сгенерировать PNG-аватар: первая буква имени на однотонном фоне.

    Цвет фона выбирается случайно из палитры; буква рисуется белым крупным
    шрифтом по центру. Возвращает Django ``ContentFile``, готовый к сохранению.
    """
    rng = random.Random(seed) if seed is not None else random
    background = rng.choice(AVATAR_PALETTE)
    image = Image.new("RGB", (AVATAR_SIZE, AVATAR_SIZE), background)
    draw = ImageDraw.Draw(image)

    char = (letter or AVATAR_FALLBACK_LETTER).strip()[:1].upper() or AVATAR_FALLBACK_LETTER
    font = _load_font()

    bbox = draw.textbbox((0, 0), char, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (AVATAR_SIZE - text_w) / 2 - bbox[0]
    y = (AVATAR_SIZE - text_h) / 2 - bbox[1]
    draw.text((x, y), char, fill=AVATAR_TEXT_COLOR, font=font)

    buffer = io.BytesIO()
    image.save(buffer, format=AVATAR_IMAGE_FORMAT, optimize=True)
    return ContentFile(buffer.getvalue())


def _load_font() -> ImageFont.ImageFont:
    """Подобрать TTF-шрифт для буквы аватара. Падает обратно на дефолтный."""
    target_size = int(AVATAR_SIZE * AVATAR_FONT_SIZE_RATIO)
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size=target_size)
        except OSError:
            continue
    return ImageFont.load_default()

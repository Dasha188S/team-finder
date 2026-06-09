"""Вспомогательные утилиты приложения users."""
import io
import random

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

# Палитра приглушённых тёмных цветов: на них хорошо читается белая буква.
AVATAR_PALETTE = (
    "#1f6feb", "#388bfd", "#0969da", "#1a7f37", "#2da44e",
    "#9a6700", "#bc4c00", "#8250df", "#a475f9", "#cf222e",
    "#d1242f", "#0a3069", "#116329", "#7d4e00", "#82071e",
)

AVATAR_SIZE = 256


def generate_avatar(letter: str, *, seed: str | None = None) -> ContentFile:
    """Сгенерировать PNG-аватар с заглавной буквой `letter` на однотонном фоне.

    Цвет фона выбирается случайно из палитры; буква рисуется белым крупным
    шрифтом по центру. Возвращает Django ContentFile, готовый к сохранению.
    """
    rng = random.Random(seed) if seed is not None else random
    background = rng.choice(AVATAR_PALETTE)
    image = Image.new("RGB", (AVATAR_SIZE, AVATAR_SIZE), background)
    draw = ImageDraw.Draw(image)

    char = (letter or "?").strip()[:1].upper() or "?"
    font = _load_font()

    bbox = draw.textbbox((0, 0), char, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (AVATAR_SIZE - text_w) / 2 - bbox[0]
    y = (AVATAR_SIZE - text_h) / 2 - bbox[1]
    draw.text((x, y), char, fill="#ffffff", font=font)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return ContentFile(buffer.getvalue())


def _load_font() -> ImageFont.ImageFont:
    """Подобрать шрифт для буквы аватара. Падает обратно на дефолтный."""
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=int(AVATAR_SIZE * 0.55))
        except OSError:
            continue
    return ImageFont.load_default()

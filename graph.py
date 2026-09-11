"""📊 График баланса как PNG"""
import io
import os

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def make_balance_graph(balance_history, width=600, height=300):
    """
    Создаёт PNG-график баланса.
    balance_history: список чисел [1000, 1200, 800, ...]
    """
    if not HAS_PIL:
        return None

    img = Image.new('RGB', (width, height), (13, 0, 26))
    draw = ImageDraw.Draw(img)

    # Рамка
    draw.rectangle([0, 0, width-1, height-1], outline=(255, 215, 0), width=2)

    if not balance_history or len(balance_history) < 2:
        # Заглушка
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        draw.text((width//2 - 100, height//2), "Сыграй игры, чтобы увидеть график",
                  fill=(150, 150, 150), font=font)
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        buf.seek(0)
        return buf

    # Оси
    pad = 40
    graph_w = width - pad * 2
    graph_h = height - pad * 2

    min_v = min(balance_history)
    max_v = max(balance_history)
    rng = max_v - min_v or 1

    # Сетка
    for i in range(5):
        y = pad + (graph_h // 4) * i
        draw.line([(pad, y), (width-pad, y)], fill=(60, 0, 80), width=1)

    # Точки
    points = []
    for i, v in enumerate(balance_history):
        x = pad + int((i / (len(balance_history)-1)) * graph_w)
        y = pad + graph_h - int(((v - min_v) / rng) * graph_h)
        points.append((x, y))

    # Линия
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=(0, 255, 136), width=3)

    # Точки
    for x, y in points:
        draw.ellipse([x-3, y-3, x+3, y+3], fill=(255, 215, 0))

    # Метки
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    draw.text((pad, 5), f"Макс: {max_v}$", fill=(255, 215, 0), font=font)
    draw.text((pad, height - 20), f"Мин: {min_v}$", fill=(255, 100, 100), font=font)
    draw.text((width - 120, 5), f"Текущий: {balance_history[-1]}$", fill=(0, 255, 136), font=font)

    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    return buf

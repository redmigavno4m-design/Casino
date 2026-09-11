import io

try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def make_balance_graph(history, width=600, height=300):
    if not HAS_PIL:
        return None
    img = Image.new('RGB', (width, height), (13, 0, 26))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width-1, height-1], outline=(255, 215, 0), width=2)

    if not history or len(history) < 2:
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        buf.seek(0)
        return buf

    pad = 40
    gw = width - pad * 2
    gh = height - pad * 2
    mn, mx = min(history), max(history)
    rng = mx - mn or 1

    for i in range(5):
        y = pad + (gh // 4) * i
        draw.line([(pad, y), (width-pad, y)], fill=(60, 0, 80), width=1)

    points = []
    for i, v in enumerate(history):
        x = pad + int((i / (len(history)-1)) * gw)
        y = pad + gh - int(((v - mn) / rng) * gh)
        points.append((x, y))

    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=(0, 255, 136), width=3)
    for x, y in points:
        draw.ellipse([x-3, y-3, x+3, y+3], fill=(255, 215, 0))

    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    return buf

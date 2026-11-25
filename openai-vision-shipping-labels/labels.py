"""Draw six fictional shipping labels with Pillow.

Four are clean labels in different carrier layouts; two are hard on purpose:
one has an ink smear across the tracking number, the other is small,
low-contrast, rotated and skewed. The generator is deterministic, so the
expected values in EXPECTED always match the pixels.

Carriers, tracking formats and addresses are invented.
"""

import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DATA_DIR = Path(__file__).parent / "data"

FONTS = {
    "mono": ["/System/Library/Fonts/Supplemental/Courier New.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
    "mono_bold": ["/System/Library/Fonts/Supplemental/Courier New Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"],
    "sans": ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "sans_bold": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
}


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for path in FONTS[kind]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)  # bitmap fallback so the script runs anywhere


@dataclass(frozen=True)
class Label:
    """What the label really says: the ground truth the test suite checks."""

    file: str
    kind: str
    carrier: str
    service_level: str
    tracking_number: str  # as printed
    sender_postcode: str
    recipient_postcode: str
    weight_kg: float


# Ground truth. `tracking_number` is as printed; the app strips spaces/hyphens.
EXPECTED = [
    Label("label_01_swiftpost.png", "clean ground label, German postcodes", "Swiftpost", "Ground",
          "SP 4821 7730 19", "10115", "80331", 2.4),
    Label("label_02_northline.png", "clean overnight label, UK postcodes", "Northline Express", "Overnight",
          "NL-9923-4410-AB", "SW1A 1AA", "M1 4BT", 12.8),
    Label("label_03_parcelwing.png", "US label, weight printed in pounds", "ParcelWing", "Economy",
          "PW770021884US", "94107", "10001", 2.27),
    Label("label_04_kestrel.png", "Dutch postcodes, tracking on a barcode strip", "Kestrel Freight", "Priority",
          "KF0057312648NL", "1012 AB", "3011 CD", 7.5),
    Label("label_05_smudged.png", "ink smear across the tracking number", "Swiftpost", "Express",
          "SP 7306 1158 42", "20095", "50667", 1.1),
    Label("label_06_rotated.png", "small, low contrast, rotated and skewed", "Northline Express", "Economy",
          "NL-3318-9072-QZ", "EH1 1YZ", "BS1 4DJ", 4.6),
]


def barcode(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, seed: str, fill=(0, 0, 0)) -> None:
    rng = random.Random(seed)
    cx = x
    while cx < x + w:
        bar = rng.choice([2, 2, 3, 4])
        d.rectangle((cx, y, cx + bar - 1, y + h), fill=fill)
        cx += bar + rng.choice([2, 3, 4])


def block(d, x, y, title, lines, fnt_t, fnt_b, fill=(20, 20, 20)) -> int:
    d.text((x, y), title, font=fnt_t, fill=(110, 110, 110))
    y += fnt_t.size + 6
    for line in lines:
        d.text((x, y), line, font=fnt_b, fill=fill)
        y += fnt_b.size + 6
    return y


def standard_label(lb: Label, brand_rgb, w=700, h=520, shade=255, ink=(15, 15, 15)) -> Image.Image:
    img = Image.new("RGB", (w, h), (shade, shade, shade))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, 78), fill=brand_rgb)
    d.text((24, 16), lb.carrier.upper(), font=font("sans_bold", 40), fill=(255, 255, 255))
    d.text((w - 24 - d.textlength(lb.service_level.upper(), font=font("sans_bold", 34)), 20),
           lb.service_level.upper(), font=font("sans_bold", 34), fill=(255, 255, 255))
    small, body = font("sans", 17), font("mono_bold", 26)
    block(d, 24, 98, "FROM", ["Orchard Supply GmbH", f"Sender postcode {lb.sender_postcode}"], small, body, ink)
    block(d, 24, 210, "TO", ["R. Okonkwo", f"Recipient postcode {lb.recipient_postcode}"], small, body, ink)
    d.text((w - 220, 98), "WEIGHT", font=small, fill=(110, 110, 110))
    d.text((w - 220, 124), f"{lb.weight_kg:.1f} kg", font=font("sans_bold", 40), fill=ink)
    d.line((24, 330, w - 24, 330), fill=ink, width=3)
    d.text((24, 346), "TRACKING", font=small, fill=(110, 110, 110))
    d.text((24, 372), lb.tracking_number, font=font("mono_bold", 40), fill=ink)
    barcode(d, 24, 430, w - 48, 60, lb.tracking_number, fill=ink)
    return img


def label_swiftpost(path: Path) -> None:
    standard_label(EXPECTED[0], (200, 30, 40)).save(path)


def label_northline(path: Path) -> None:
    standard_label(EXPECTED[1], (20, 60, 120)).save(path)


def label_parcelwing(path: Path) -> None:
    """Weight is printed in pounds only: the model must convert to kg."""
    lb = EXPECTED[2]
    img = standard_label(lb, (20, 120, 80))
    d = ImageDraw.Draw(img)
    d.rectangle((470, 118, 700, 180), fill=(255, 255, 255))  # wipe the kg weight drawn by the template
    d.text((480, 124), "WT 5.0 lb", font=font("sans_bold", 38), fill=(15, 15, 15))
    img.save(path)


def label_kestrel(path: Path) -> None:
    """Different layout: dark side bar, stacked addresses, tracking under the barcode."""
    lb = EXPECTED[3]
    w, h = 760, 480
    img = Image.new("RGB", (w, h), (250, 250, 246))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 150, h), fill=(35, 35, 40))
    d.text((18, 30), "KESTREL", font=font("sans_bold", 26), fill=(240, 200, 60))
    d.text((18, 66), "FREIGHT", font=font("sans_bold", 26), fill=(240, 200, 60))
    d.text((18, 400), lb.service_level.upper(), font=font("sans_bold", 20), fill=(255, 255, 255))
    small, body = font("sans", 16), font("sans_bold", 25)
    block(d, 180, 30, "SHIPPER", ["Veldkamp Bloemen BV", f"Postcode: {lb.sender_postcode}"], small, body)
    block(d, 180, 140, "CONSIGNEE", ["L. de Wit", f"Postcode: {lb.recipient_postcode}"], small, body)
    d.text((560, 30), "GROSS WEIGHT", font=small, fill=(110, 110, 110))
    d.text((560, 54), f"{lb.weight_kg:.1f} kg", font=font("sans_bold", 36), fill=(15, 15, 15))
    barcode(d, 180, 270, 540, 90, lb.tracking_number)
    d.text((180, 372), lb.tracking_number, font=font("mono_bold", 34), fill=(15, 15, 15))
    img.save(path)


def label_smudged(path: Path) -> None:
    """A wet-ink smear drags across the last digits of the tracking number."""
    lb = EXPECTED[4]
    img = standard_label(lb, (200, 30, 40), shade=248)
    smear = Image.new("RGB", img.size, (248, 248, 248))
    sd = ImageDraw.Draw(smear)
    sd.rectangle((200, 362, 400, 420), fill=(90, 90, 95))
    smear = smear.filter(ImageFilter.GaussianBlur(9))
    # Darken only where the smear is, so the digits underneath stay half visible.
    px_img, px_smear = img.load(), smear.load()
    for y in range(340, 440):
        for x in range(180, 430):
            s = px_smear[x, y][0]
            if s < 245:
                r, g, b = px_img[x, y]
                k = s / 248
                px_img[x, y] = (int(r * k * 0.8), int(g * k * 0.8), int(b * k * 0.8))
    img.filter(ImageFilter.GaussianBlur(0.8)).save(path)


def label_rotated(path: Path) -> None:
    """Small, faded label photographed sideways and slightly skewed."""
    lb = EXPECTED[5]
    img = standard_label(lb, (90, 105, 135), shade=226, ink=(95, 95, 100))
    img = img.resize((490, 364))
    img = img.rotate(90, expand=True, fillcolor=(190, 190, 190))
    img = img.rotate(8, expand=True, fillcolor=(190, 190, 190), resample=Image.BICUBIC)
    img.filter(ImageFilter.GaussianBlur(1.1)).save(path)


GENERATORS = [label_swiftpost, label_northline, label_parcelwing, label_kestrel, label_smudged, label_rotated]


def generate_labels(force: bool = False) -> list[Path]:
    """Write the six PNGs into data/ (skipped if they exist) and return their paths."""
    DATA_DIR.mkdir(exist_ok=True)
    paths = []
    for lb, gen in zip(EXPECTED, GENERATORS):
        path = DATA_DIR / lb.file
        if force or not path.exists():
            gen(path)
        paths.append(path)
    return paths


if __name__ == "__main__":
    for p in generate_labels(force=True):
        print(p)

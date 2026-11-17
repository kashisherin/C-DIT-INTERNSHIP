from pathlib import Path
from PIL import Image, ImageOps

BASE_DIR = Path(__file__).resolve().parent

images = {
    "FAILING RATION IMAGE":
        BASE_DIR / "en_05_ration.jpg",

    "WORKING KSEB IMAGE":
        BASE_DIR / "grievance_storage" /
        "departments" / "KSEB" /
        "GRV-KSEB-0001" / "original.jpg"
}

for label, path in images.items():

    print("\n" + "=" * 50)
    print(label)
    print("=" * 50)

    if not path.exists():
        print("FILE NOT FOUND:", path)
        continue

    print("Path:", path)
    print("File size:", round(path.stat().st_size / 1024, 2), "KB")

    try:
        with Image.open(path) as image:
            print("Format:", image.format)
            print("Original dimensions:", image.size)
            print("Image mode:", image.mode)

            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")

            print("Normalized dimensions:", image.size)

            print("PNG size after normalization:", end=" ")

            from io import BytesIO
            buffer = BytesIO()
            image.save(buffer, format="PNG")

            print(round(len(buffer.getvalue()) / 1024, 2), "KB")

    except Exception as error:
        print("IMAGE ERROR:", error)
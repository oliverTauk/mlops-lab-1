"""Prepare Food-11 for training.

Reads   data/food11_raw/{training,validation,evaluation}/<label>_<n>.jpg
Writes  data/food11_processed/<split>/<Category name>/<file>.jpg       (128x128)
        data/food11_processed_mini/<split>/<Category name>/<file>.jpg  (<=100 per class)

This is the "ImageFolder" layout (root/split/class/image) that torchvision
expects when training ResNet and other image classifiers.

Run with:  uv run python ./src/food11/data.py
"""

from __future__ import annotations

import shutil
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

# --- Configuration ----------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "food11_raw"
PROCESSED_DIR = DATA_DIR / "food11_processed"
MINI_DIR = DATA_DIR / "food11_processed_mini"

SPLITS = ["training", "validation", "evaluation"]
IMAGE_SIZE = (128, 128)
MINI_PER_CLASS = 100
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

CLASSES = [
    "Bread",
    "Dairy product",
    "Dessert",
    "Egg",
    "Fried food",
    "Meat",
    "Noodles-Pasta",
    "Rice",
    "Seafood",
    "Soup",
    "Vegetable-Fruit",
]


# --- Helpers ----------------------------------------------------------------

def label_from_filename(path: Path) -> int:
    """'3_125.jpg' -> 3. The category index is the part before the underscore."""
    return int(path.stem.split("_")[0])


def resize_image(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img = img.convert("RGB")
        img = img.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)
        img.save(dst.with_suffix(".jpg"), "JPEG", quality=95)


def reset_dir(path: Path) -> None:
    """Start from a clean folder so re-running the script is reproducible."""
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


# --- Main steps -------------------------------------------------------------

def build_processed() -> None:
    reset_dir(PROCESSED_DIR)
    jobs: list[tuple[Path, Path]] = []

    for split in SPLITS:
        split_dir = RAW_DIR / split
        if not split_dir.is_dir():
            raise FileNotFoundError(f"Missing raw split folder: {split_dir}")

        for src in sorted(split_dir.iterdir()):
            if src.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            class_name = CLASSES[label_from_filename(src)]
            dst = PROCESSED_DIR / split / class_name / src.name
            jobs.append((src, dst))

    print(f"Resizing {len(jobs)} images to {IMAGE_SIZE[0]}x{IMAGE_SIZE[1]} ...")
    with ThreadPoolExecutor() as pool:
        list(pool.map(lambda job: resize_image(*job), jobs))


def build_mini() -> None:
    reset_dir(MINI_DIR)
    counts: dict[tuple[str, str], int] = defaultdict(int)

    for split in SPLITS:
        for class_dir in sorted((PROCESSED_DIR / split).iterdir()):
            if not class_dir.is_dir():
                continue
            images = sorted(class_dir.iterdir())[:MINI_PER_CLASS]
            target = MINI_DIR / split / class_dir.name
            target.mkdir(parents=True, exist_ok=True)
            for img in images:
                shutil.copy2(img, target / img.name)
            counts[(split, class_dir.name)] = len(images)

    print("Mini dataset built:")
    for (split, class_name), n in sorted(counts.items()):
        print(f"  {split:<11} {class_name:<16} {n}")


def main() -> None:
    build_processed()
    build_mini()
    print("Done.")


if __name__ == "__main__":
    main()

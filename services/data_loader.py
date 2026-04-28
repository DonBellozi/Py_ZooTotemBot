import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename: str):
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_animals() -> dict:
    animals = load_json("animals.json")
    return {animal["id"]: animal for animal in animals}


def load_questions() -> list[dict]:
    return load_json("questions.json")

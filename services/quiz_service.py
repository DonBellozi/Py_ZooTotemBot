from collections import defaultdict
import random


def create_empty_scores(animals: dict) -> dict[str, int]:
    return {animal_id: 0 for animal_id in animals.keys()}


def apply_scores(current_scores: dict[str, int], answer_scores: dict[str, int]) -> dict[str, int]:
    """
    Добавляет баллы выбранного ответа к текущему счету пользователя.
    """
    updated_scores = defaultdict(int, current_scores)

    for animal_id, points in answer_scores.items():
        updated_scores[animal_id] += points

    return dict(updated_scores)


def get_result_animal_id(scores: dict[str, int]) -> str:
    """
    Возвращает животное с максимальным количеством баллов.
    Если лидеров несколько, выбирает случайного из них.
    """
    if not scores:
        raise ValueError("Невозможно определить результат: список баллов пуст")

    max_score = max(scores.values())
    leaders = [animal_id for animal_id, score in scores.items() if score == max_score]

    return random.choice(leaders)

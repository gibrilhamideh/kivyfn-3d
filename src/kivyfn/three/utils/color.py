import random


def random_color() -> list[float]:
    return [
        random.random(),
        random.random(),
        random.random(),
        1.0,
    ]

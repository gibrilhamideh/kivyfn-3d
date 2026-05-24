# kivyfn/three/utils/stopwatch.py

from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Iterator


class Stopwatch:

    _records: list[tuple[str, float]] = []

    @classmethod
    @contextmanager
    def section(
        cls,
        name: str,
    ) -> Iterator[None]:
        start = perf_counter()

        try:
            yield

        finally:
            elapsed = perf_counter() - start

            cls._records.append(
                (name, elapsed)
            )

            print(
                f"[STOPWATCH] "
                f"{name}: {elapsed:.4f}s"
            )

    @classmethod
    def summary(cls) -> None:
        total = sum(
            elapsed
            for _, elapsed in cls._records
        )

        print("\n[STOPWATCH SUMMARY]")
        print("-" * 50)

        for name, elapsed in cls._records:
            percent = (
                (elapsed / total) * 100.0
                if total
                else 0.0
            )

            print(
                f"{name:<32}"
                f"{elapsed:>8.4f}s"
                f" {percent:>6.2f}%"
            )

        print("-" * 50)

        print(
            f"{'TOTAL':<32}"
            f"{total:>8.4f}s"
        )

    @classmethod
    def clear(cls) -> None:
        cls._records.clear()

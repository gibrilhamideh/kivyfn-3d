# kivyfn/three/utils/stopwatch.py

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter
from typing import Iterator


@dataclass(slots=True)
class StopwatchStat:
    count: int = 0
    total: float = 0.0
    max: float = 0.0
    last: float = 0.0


class Stopwatch:
    enabled: bool = True

    _stats: dict[str, StopwatchStat] = {}
    _counters: dict[str, int] = {}

    @classmethod
    @contextmanager
    def section(
        cls,
        name: str,
    ) -> Iterator[None]:
        if not cls.enabled:
            yield
            return

        start = perf_counter()

        try:
            yield
        finally:
            cls.add_time(
                name,
                perf_counter() - start,
            )

    @classmethod
    def add_time(
        cls,
        name: str,
        elapsed: float,
    ) -> None:
        if not cls.enabled:
            return

        stat = cls._stats.setdefault(
            name,
            StopwatchStat(),
        )

        stat.count += 1
        stat.total += elapsed
        stat.last = elapsed

        if elapsed > stat.max:
            stat.max = elapsed

    @classmethod
    def add_count(
        cls,
        name: str,
        value: int,
    ) -> None:
        if not cls.enabled:
            return

        cls._counters[name] = cls._counters.get(name, 0) + value

    @classmethod
    def summary(
        cls,
        *,
        clear: bool = False,
        min_ms: float = 0.0,
    ) -> None:
        if not cls._stats and not cls._counters:
            return

        print("\n[STOPWATCH SUMMARY]")
        print("-" * 86)
        print(
            f"{'name':<38}"
            f"{'total ms':>12}"
            f"{'avg ms':>12}"
            f"{'max ms':>12}"
            f"{'last ms':>12}"
            f"{'count':>8}"
        )
        print("-" * 86)

        for name, stat in sorted(
            cls._stats.items(),
            key=lambda item: item[1].total,
            reverse=True,
        ):
            total_ms = stat.total * 1000.0

            if total_ms < min_ms:
                continue

            avg_ms = total_ms / stat.count if stat.count else 0.0

            print(
                f"{name:<38}"
                f"{total_ms:>12.3f}"
                f"{avg_ms:>12.3f}"
                f"{stat.max * 1000.0:>12.3f}"
                f"{stat.last * 1000.0:>12.3f}"
                f"{stat.count:>8}"
            )

        if cls._counters:
            print("-" * 86)
            print("[COUNTERS]")

            for name, value in sorted(cls._counters.items()):
                print(
                    f"{name:<38}"
                    f"{value:>12}"
                )

        print("-" * 86)

        if clear:
            cls.clear()

    @classmethod
    def clear(
        cls,
    ) -> None:
        cls._stats.clear()
        cls._counters.clear()

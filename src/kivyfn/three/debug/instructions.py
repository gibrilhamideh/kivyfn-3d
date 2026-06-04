# kivyfn/three/utils/instructions.py

from __future__ import annotations

from collections.abc import Iterator

from kivy.graphics import BindTexture
from kivy.graphics.instructions import Instruction


def walk_instructions(
    instruction: Instruction,
    *,
    level: int = 0,
) -> Iterator[tuple[Instruction, int]]:

    yield instruction, level

    if not hasattr(instruction, "children"):
        return

    for child in instruction.children:  # pyright: ignore[reportAttributeAccessIssue]
        yield from walk_instructions(
            child,
            level=level + 1,
        )


def debug_instructions(
    instruction: Instruction,
    *,
    level: int = 0,
) -> None:

    indent = "  " * level

    info = (
        f"{indent}- "
        f"{instruction.__class__.__name__}: "
        f"{instruction}"
    )

    if isinstance(instruction, BindTexture):
        slot = getattr(
            instruction,
            "index",
            "Unknown Slot",
        )

        source = getattr(
            instruction,
            "source",
            "No Source",
        )

        info += (
            f" [Slot/Index: {slot}"
            f" | Source: {source!r}]"
        )

    print(info)

    if not hasattr(instruction, "children"):
        return

    for child in instruction.children:  # pyright: ignore[reportAttributeAccessIssue]
        debug_instructions(
            child,
            level=level + 1,
        )

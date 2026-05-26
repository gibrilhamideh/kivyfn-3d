# kivyfn/three/render/manager.py
from __future__ import annotations
from typing import TYPE_CHECKING

from dataclasses import dataclass, field
from typing import Any

if TYPE_CHECKING:
    from kivyfn.three.render.context import RenderContext


@dataclass(slots=True)
class ManagedRenderContext:
    name: str
    context: RenderContext
    tags: set[str] = field(default_factory=set)


class RenderContextManager:
    def __init__(self) -> None:
        self._contexts: dict[str, ManagedRenderContext] = {}

    def __len__(self) -> int:
        return len(self._contexts)

    def add(
        self,
        name: str,
        context: RenderContext,
        *,
        tags: set[str] | None = None,
    ) -> None:
        if name in self._contexts:
            raise ValueError(f"Render context already exists: {name!r}")

        self._contexts[name] = ManagedRenderContext(
            name=name,
            context=context,
            tags=set(tags or ()),
        )

    def remove(self, name: str) -> RenderContext | None:
        managed = self._contexts.pop(name, None)

        if managed is None:
            return None

        return managed.context

    def get(self, name: str) -> RenderContext:
        try:
            return self._contexts[name].context
        except KeyError:
            raise KeyError(f"Render context does not exist: {name!r}") from None

    def exists(self, name: str) -> bool:
        return name in self._contexts

    def names(self) -> list[str]:
        return list(self._contexts.keys())

    def values(self) -> list[RenderContext]:
        return [
            managed.context
            for managed in self._contexts.values()
        ]

    def items(self) -> list[tuple[str, RenderContext]]:
        return [
            (name, managed.context)
            for name, managed in self._contexts.items()
        ]

    def set_uniform(
        self,
        context_name: str,
        uniform_name: str,
        value: Any,
    ) -> None:
        context = self.get(context_name)
        context.ctx[uniform_name] = value

    def set_uniform_all(
        self,
        uniform_name: str,
        value: Any,
        *,
        whitelist: set[str] | None = None,
        blacklist: set[str] | None = None,
    ) -> None:
        for name, managed in self._contexts.items():
            if whitelist is not None and name not in whitelist:
                continue

            if blacklist is not None and name in blacklist:
                continue

            managed.context.ctx[uniform_name] = value

    def set_uniform_by_tag(
        self,
        tag: str,
        uniform_name: str,
        value: Any,
    ) -> None:
        for managed in self._contexts.values():
            if tag not in managed.tags:
                continue

            managed.context.ctx[uniform_name] = value

    def add_tag(
        self,
        context_name: str,
        tag: str,
    ) -> None:
        self._contexts[context_name].tags.add(tag)

    def remove_tag(
        self,
        context_name: str,
        tag: str,
    ) -> None:
        self._contexts[context_name].tags.discard(tag)

    def get_tags(
        self,
        context_name: str,
    ) -> set[str]:
        return set(self._contexts[context_name].tags)

    def clear(self) -> None:
        self._contexts.clear()

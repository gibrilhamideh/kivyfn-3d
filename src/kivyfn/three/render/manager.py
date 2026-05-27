# kivyfn/three/render/manager.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kivyfn.three.render.context import RenderContext


FRAMEBUFFER_TEXTURE_START_SLOT = 10


@dataclass(slots=True)
class ManagedRenderContext:
    name: str
    context: RenderContext
    tags: set[str] = field(default_factory=set)


@dataclass(slots=True)
class FramebufferLink:
    source: str
    output: str
    uniform: str
    slot: int
    tags: set[str] = field(default_factory=set)
    names: set[str] = field(default_factory=set)


class RenderContextManager:
    def __init__(self) -> None:
        self._contexts: dict[str, ManagedRenderContext] = {}
        self._framebuffer_links: list[FramebufferLink] = []

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

    def select(
        self,
        *,
        tags: set[str] | None = None,
        names: set[str] | None = None,
    ) -> list[RenderContext]:
        selected: list[RenderContext] = []

        for name, managed in self._contexts.items():
            if names is not None and name not in names:
                continue

            if tags is not None and not tags.intersection(managed.tags):
                continue

            selected.append(managed.context)

        return selected

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

    def reserve_texture_slot(
        self,
        *,
        source: str,
        output: str,
        uniform: str,
        tags: set[str] | None = None,
        names: set[str] | None = None,
    ) -> int:
        tag_set = set(tags or ())
        name_set = set(names or ())

        for link in self._framebuffer_links:
            if (
                link.source == source
                and link.output == output
                and link.uniform == uniform
                and link.tags == tag_set
                and link.names == name_set
            ):
                return link.slot

        used_slots = {
            link.slot
            for link in self._framebuffer_links
        }

        slot = FRAMEBUFFER_TEXTURE_START_SLOT

        while slot in used_slots:
            slot += 1

        self._framebuffer_links.append(
            FramebufferLink(
                source=source,
                output=output,
                uniform=uniform,
                slot=slot,
                tags=tag_set,
                names=name_set,
            )
        )

        return slot

    def release_texture_links(
        self,
        *,
        source: str,
        tags: set[str] | None = None,
        names: set[str] | None = None,
    ) -> list[FramebufferLink]:
        released: list[FramebufferLink] = []
        remaining: list[FramebufferLink] = []

        tag_set = set(tags or ())
        name_set = set(names or ())

        for link in self._framebuffer_links:
            if link.source != source:
                remaining.append(link)
                continue

            if tags is not None and link.tags != tag_set:
                remaining.append(link)
                continue

            if names is not None and link.names != name_set:
                remaining.append(link)
                continue

            released.append(link)

        self._framebuffer_links = remaining
        return released

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
        self._framebuffer_links.clear()

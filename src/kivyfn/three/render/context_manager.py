# kivyfn/three/render/context_manager.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kivyfn.three.render.context import RenderContext
from kivyfn.three.render.shader import Shader


RENDER_PASS_TEXTURE_START_SLOT = 10


@dataclass(slots=True)
class ManagedRenderContext:
    name: str
    context: RenderContext
    tags: set[str] = field(default_factory=set)


@dataclass(slots=True)
class RenderPassLink:
    source: str
    output: str
    uniform: str
    slot: int
    tags: set[str] = field(default_factory=set)
    names: set[str] = field(default_factory=set)


class RenderContextManager:
    def __init__(self) -> None:
        self._contexts: dict[str, ManagedRenderContext] = {}
        self._hidden: set[str] = set()
        self._render_pass_links: list[RenderPassLink] = []

    def __len__(self) -> int:
        return len(self._contexts)

    # =================================== #
    # Context Lifecycle
    # =================================== #
    def create(
        self,
        name: str,
        shader: Shader,
        *,
        hot_reload: bool = False,
        framebuffer: bool = False,
        size: tuple[int, int] | None = None,
        tags: set[str] | None = None,
    ) -> RenderContext:
        if name in self._contexts:
            raise ValueError(f"Render context already exists: {name!r}")

        context = RenderContext(
            name=name,
            shader=shader,
            hot_reload=hot_reload,
            framebuffer=framebuffer,
            size=size,
        )

        self._contexts[name] = ManagedRenderContext(
            name=name,
            context=context,
            tags=set(tags or ()),
        )

        return context

    def destroy(self, name: str) -> RenderContext | None:
        managed = self._contexts.pop(name, None)
        self._hidden.discard(name)

        if managed is None:
            return None

        return managed.context

    # =================================== #
    # Hidden State
    # =================================== #
    def hidden(self, name: str) -> bool:
        return name in self._hidden

    def set_hidden(
        self,
        name: str,
        hidden: bool,
    ) -> None:
        if name not in self._contexts:
            raise KeyError(f"Render context does not exist: {name!r}")

        if hidden:
            self._hidden.add(name)
        else:
            self._hidden.discard(name)

    def hidden_names(self) -> list[str]:
        return list(self._hidden)

    def visible_names(self) -> list[str]:
        return [
            name
            for name in self._contexts
            if name not in self._hidden
        ]

    def hidden_contexts(self) -> list[RenderContext]:
        return [
            self._contexts[name].context
            for name in self._hidden
            if name in self._contexts
        ]

    def visible_contexts(self) -> list[RenderContext]:
        return [
            managed.context
            for name, managed in self._contexts.items()
            if name not in self._hidden
        ]

    # =================================== #
    # Access
    # =================================== #
    def get(self, name: str) -> RenderContext:
        try:
            return self._contexts[name].context
        except KeyError:
            raise KeyError(f"Render context does not exist: {name!r}") from None

    def exists(self, name: str) -> bool:
        return name in self._contexts

    # =================================== #
    # Iteration
    # =================================== #
    def names(
        self,
        *,
        include_hidden: bool = True,
    ) -> list[str]:
        if include_hidden:
            return list(self._contexts.keys())

        return self.visible_names()

    def values(
        self,
        *,
        include_hidden: bool = True,
    ) -> list[RenderContext]:
        if include_hidden:
            return [
                managed.context
                for managed in self._contexts.values()
            ]

        return self.visible_contexts()

    def items(
        self,
        *,
        include_hidden: bool = True,
    ) -> list[tuple[str, RenderContext]]:
        return [
            (name, managed.context)
            for name, managed in self._contexts.items()
            if include_hidden or name not in self._hidden
        ]

    def select(
        self,
        *,
        tags: set[str] | None = None,
        names: set[str] | None = None,
        include_hidden: bool = True,
    ) -> list[RenderContext]:
        selected: list[RenderContext] = []

        for name, managed in self._contexts.items():
            if not include_hidden and name in self._hidden:
                continue

            if names is not None and name not in names:
                continue

            if tags is not None and not tags.intersection(managed.tags):
                continue

            selected.append(managed.context)

        return selected

    # =================================== #
    # Uniforms
    # =================================== #
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
        include_hidden: bool = True,
    ) -> None:
        for name, managed in self._contexts.items():
            if not include_hidden and name in self._hidden:
                continue

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
        *,
        include_hidden: bool = True,
    ) -> None:
        for name, managed in self._contexts.items():
            if not include_hidden and name in self._hidden:
                continue

            if tag not in managed.tags:
                continue

            managed.context.ctx[uniform_name] = value

    # =================================== #
    # Render Pass Texture Slots
    # =================================== #
    def reserve_render_pass_slot(
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

        for link in self._render_pass_links:
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
            for link in self._render_pass_links
        }

        slot = RENDER_PASS_TEXTURE_START_SLOT

        while slot in used_slots:
            slot += 1

        self._render_pass_links.append(
            RenderPassLink(
                source=source,
                output=output,
                uniform=uniform,
                slot=slot,
                tags=tag_set,
                names=name_set,
            )
        )

        return slot

    # =================================== #
    # Tags
    # =================================== #
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

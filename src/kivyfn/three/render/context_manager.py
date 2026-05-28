# kivyfn/three/render/context_manager.py

from __future__ import annotations
from typing import Literal

from dataclasses import dataclass, field

from kivyfn.three.render.context import RenderContext
from kivyfn.three.render.shader import Shader


RenderPassOutput = Literal[
    "depth",
    "normal",
    "position",
    "id",
    "color"
]

RENDER_PASS_TEXTURE_START_SLOT = 10




@dataclass(slots=True)
class ManagedRenderContext:
    name: str
    context: RenderContext
    tags: set[str] = field(default_factory=set)


@dataclass(slots=True)
class RenderPassLink:
    target: str
    source: str
    output: RenderPassOutput
    uniform: str
    slot: int


class RenderContextManager:
    def __init__(self) -> None:
        self._contexts: dict[str, ManagedRenderContext] = {}
        self._passes: dict[str, ManagedRenderContext] = {}
        self._hidden: set[str] = set()
        self._render_pass_links: dict[str, list[RenderPassLink]] = {}

    def __len__(self) -> int:
        return len(self._contexts)

    # =================================== #
    # General
    # =================================== #
    def get(
        self,
        name: str,
    ) -> RenderContext:
        if name in self._contexts:
            return self._contexts[name].context

        if name in self._passes:
            return self._passes[name].context

        raise KeyError(f"Render context does not exist: {name!r}")

    # =================================== #
    # Contexts
    # =================================== #
    def create_context(
        self,
        name: str,
        shader: Shader,
        *,
        hot_reload: bool = False,
        tags: set[str] | None = None,
    ) -> RenderContext:
        self._ensure_name_available(name)

        context = RenderContext(
            name=name,
            shader=shader,
            hot_reload=hot_reload,
            framebuffer=False,
        )

        self._contexts[name] = ManagedRenderContext(
            name=name,
            context=context,
            tags=set(tags or ()),
        )

        return context

    def destroy_context(
        self,
        name: str,
    ) -> RenderContext | None:
        managed = self._contexts.pop(name, None)

        if managed is None:
            return None

        self._hidden.discard(name)
        self._render_pass_links.pop(name, None)

        return managed.context

    def get_context(
        self,
        name: str,
    ) -> RenderContext:
        try:
            return self._contexts[name].context
        except KeyError:
            raise KeyError(f"Render context does not exist: {name!r}") from None

    def context_exists(
        self,
        name: str,
    ) -> bool:
        return name in self._contexts

    def hide_context(
        self,
        name: str,
    ) -> None:
        if name not in self._contexts:
            raise KeyError(f"Render context does not exist: {name!r}")

        self._hidden.add(name)

    def show_context(
        self,
        name: str,
    ) -> None:
        if name not in self._contexts:
            raise KeyError(f"Render context does not exist: {name!r}")

        self._hidden.discard(name)

    def context_hidden(
        self,
        name: str,
    ) -> bool:
        return name in self._hidden

    def context_names(
        self,
        *,
        include_hidden: bool = True,
    ) -> list[str]:
        return [
            name
            for name in self._contexts
            if include_hidden or name not in self._hidden
        ]

    def context_values(
        self,
        *,
        include_hidden: bool = True,
    ) -> list[RenderContext]:
        return [
            managed.context
            for name, managed in self._contexts.items()
            if include_hidden or name not in self._hidden
        ]

    def context_items(
        self,
        *,
        include_hidden: bool = True,
    ) -> list[tuple[str, RenderContext]]:
        return [
            (name, managed.context)
            for name, managed in self._contexts.items()
            if include_hidden or name not in self._hidden
        ]

    def select_contexts(
        self,
        *,
        tags: set[str] | None = None,
        names: set[str] | None = None,
        include_hidden: bool = True,
    ) -> list[RenderContext]:
        return self._select(
            self._contexts,
            tags=tags,
            names=names,
            include_hidden=include_hidden,
            use_hidden=True,
        )

    # =================================== #
    # Render Passes
    # =================================== #
    def create_render_pass(
        self,
        name: str,
        shader: Shader,
        *,
        size: tuple[int, int],
        hot_reload: bool = False,
        tags: set[str] | None = None,
    ) -> RenderContext:
        self._ensure_name_available(name)

        context = RenderContext(
            name=name,
            shader=shader,
            hot_reload=hot_reload,
            framebuffer=True,
            size=size,
        )

        self._passes[name] = ManagedRenderContext(
            name=name,
            context=context,
            tags=set(tags or ()),
        )

        return context

    def get_render_pass(
        self,
        name: str,
    ) -> RenderContext:
        try:
            return self._passes[name].context
        except KeyError:
            raise KeyError(f"Render pass does not exist: {name!r}") from None

    def render_pass_exists(
        self,
        name: str,
    ) -> bool:
        return name in self._passes

    def render_pass_names(self) -> list[str]:
        return list(self._passes.keys())

    def render_pass_values(self) -> list[RenderContext]:
        return [
            managed.context
            for managed in self._passes.values()
        ]

    def render_pass_items(self) -> list[tuple[str, RenderContext]]:
        return [
            (name, managed.context)
            for name, managed in self._passes.items()
        ]

    def select_render_passes(
        self,
        *,
        tags: set[str] | None = None,
        names: set[str] | None = None,
    ) -> list[RenderContext]:
        return self._select(
            self._passes,
            tags=tags,
            names=names,
            include_hidden=True,
            use_hidden=False,
        )

    # =================================== #
    # Render Pass Links
    # =================================== #
    def register_render_pass_link(
        self,
        *,
        target: str,
        source: str,
        output: RenderPassOutput,
        uniform: str,
    ) -> RenderPassLink:
        if target not in self._contexts:
            raise KeyError(f"Target context does not exist: {target!r}")

        if source not in self._passes:
            raise KeyError(f"Render pass does not exist: {source!r}")

        links = self._render_pass_links.setdefault(target, [])

        for link in links:
            if (
                link.source == source
                and link.output == output
                and link.uniform == uniform
            ):
                return link

        link = RenderPassLink(
            target=target,
            source=source,
            output=output,
            uniform=uniform,
            slot=self._next_render_pass_texture_slot(),
        )

        links.append(link)

        return link

    def get_render_pass_links(
        self,
        context_name: str,
    ) -> list[RenderPassLink]:
        return list(self._render_pass_links.get(context_name, ()))

    def render_pass_links(self) -> list[RenderPassLink]:
        return [
            link
            for links in self._render_pass_links.values()
            for link in links
        ]

    # =================================== #
    # Context Tags
    # =================================== #
    def add_context_tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        self._contexts[name].tags.add(tag)

    def remove_context_tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        self._contexts[name].tags.discard(tag)

    def get_context_tags(
        self,
        name: str,
    ) -> set[str]:
        return set(self._contexts[name].tags)

    # =================================== #
    # Render Pass Tags
    # =================================== #
    def add_render_pass_tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        self._passes[name].tags.add(tag)

    def remove_render_pass_tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        self._passes[name].tags.discard(tag)

    def get_render_pass_tags(
        self,
        name: str,
    ) -> set[str]:
        return set(self._passes[name].tags)

    # =================================== #
    # Context Uniforms
    # =================================== #
    def set_context_uniform(
        self,
        name: str,
        uniform: str,
        value,
    ) -> None:
        self.get_context(name).set_uniform(uniform, value)

    def set_context_uniform_by_tag(
        self,
        tag: str,
        uniform: str,
        value,
        *,
        include_hidden: bool = True,
    ) -> None:
        for name, managed in self._contexts.items():
            if not include_hidden and name in self._hidden:
                continue

            if tag not in managed.tags:
                continue

            managed.context.set_uniform(uniform, value)

    # =================================== #
    # Render Pass Uniforms
    # =================================== #
    def set_render_pass_uniform(
        self,
        name: str,
        uniform: str,
        value,
    ) -> None:
        self.get_render_pass(name).set_uniform(uniform, value)

    def set_render_pass_uniform_by_tag(
        self,
        tag: str,
        uniform: str,
        value,
    ) -> None:
        for managed in self._passes.values():
            if tag not in managed.tags:
                continue

            managed.context.set_uniform(uniform, value)

    # =================================== #
    # Internals
    # =================================== #
    def _ensure_name_available(
        self,
        name: str,
    ) -> None:
        if name in self._contexts:
            raise ValueError(f"Render context already exists: {name!r}")

        if name in self._passes:
            raise ValueError(f"Render pass already exists: {name!r}")

    def _select(
        self,
        store: dict[str, ManagedRenderContext],
        *,
        tags: set[str] | None,
        names: set[str] | None,
        include_hidden: bool,
        use_hidden: bool,
    ) -> list[RenderContext]:
        selected: list[RenderContext] = []

        for name, managed in store.items():
            if use_hidden and not include_hidden and name in self._hidden:
                continue

            if names is not None and name not in names:
                continue

            if tags is not None and not tags.intersection(managed.tags):
                continue

            selected.append(managed.context)

        return selected

    def _next_render_pass_texture_slot(self) -> int:
        used_slots = {
            link.slot
            for links in self._render_pass_links.values()
            for link in links
        }

        slot = RENDER_PASS_TEXTURE_START_SLOT

        while slot in used_slots:
            slot += 1

        return slot

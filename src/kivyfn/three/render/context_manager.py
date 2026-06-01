# kivyfn/three/render/context_manager.py

from __future__ import annotations
from typing import Callable
from functools import partial
from dataclasses import dataclass, field

from kivy.graphics import BindTexture
from kivy.graphics.texture import Texture

from kivyfn.three.render.context import (
    RenderContext,
    RenderPass,
    RenderPassOutput,
)
from kivyfn.three.render.context_registry import (
    ContextSelection,
    RenderContextRegistry,
    RenderPassRegistry,
)


RENDER_PASS_TEXTURE_START_SLOT = 10


# =================================== #
# Render Pass Link Models
# =================================== #

@dataclass(slots=True)
class RenderPassBinding:
    pass_name: str
    target_name: str
    output: RenderPassOutput
    uniform: str
    slot: int

    instruction: BindTexture | None = None
    texture_callback: Callable | None = None


@dataclass(slots=True)
class RenderPassLink:
    pass_name: str
    sources: ContextSelection
    targets: ContextSelection
    output: RenderPassOutput
    uniform: str
    bindings: list[RenderPassBinding] = field(default_factory=list)


# =================================== #
# Render Pass Binder
# =================================== #

class RenderPassBinder:
    def __init__(
        self,
        *,
        contexts: RenderContextRegistry,
        passes: RenderPassRegistry,
    ) -> None:
        self.contexts = contexts
        self.passes = passes

        self._links: list[RenderPassLink] = []
        self._bindings_by_target: dict[str, list[RenderPassBinding]] = {}

    # =================================== #
    # Public API
    # =================================== #

    def link(
        self,
        *,
        pass_name: str,
        uniform: str,
        output: RenderPassOutput,
        source_names: set[str] | None = None,
        source_tags: set[str] | None = None,
        target_names: set[str] | None = None,
        target_tags: set[str] | None = None,
    ) -> RenderPassLink:
        render_pass = self.passes.get(pass_name)

        sources = ContextSelection(
            names=source_names,
            tags=source_tags,
        )

        targets = ContextSelection(
            names=target_names,
            tags=target_tags,
        )

        existing = self._find_link(
            pass_name=pass_name,
            uniform=uniform,
            output=output,
            sources=sources,
            targets=targets,
        )

        if existing is not None:
            return existing

        link = RenderPassLink(
            pass_name=pass_name,
            sources=sources,
            targets=targets,
            output=output,
            uniform=uniform,
        )

        target_contexts = self.contexts.select(
            selection=targets,
            include_hidden=True,
        )

        for target_context in target_contexts:
            binding, created = self._get_or_create_binding(
                pass_name=pass_name,
                target_name=target_context.name,
                output=output,
                uniform=uniform,
            )

            link.bindings.append(binding)

            if created:
                self._attach_binding(
                    binding=binding,
                    render_pass=render_pass,
                    target_context=target_context,
                )

        self._links.append(link)

        return link

    def links(self) -> list[RenderPassLink]:
        return list(self._links)

    def links_for_pass(
        self,
        pass_name: str,
    ) -> list[RenderPassLink]:
        return [
            link
            for link in self._links
            if link.pass_name == pass_name
        ]

    def links_for_target(
        self,
        target_name: str,
    ) -> list[RenderPassLink]:
        return [
            link
            for link in self._links
            if any(
                binding.target_name == target_name
                for binding in link.bindings
            )
        ]

    def links_for_source(
        self,
        source_name: str,
    ) -> list[RenderPassLink]:
        links: list[RenderPassLink] = []

        for link in self._links:
            source_contexts = self.contexts.select(
                selection=link.sources,
                include_hidden=True,
            )

            for context in source_contexts:
                if context.name == source_name:
                    links.append(link)
                    break

        return links

    def bindings(self) -> list[RenderPassBinding]:
        return [
            binding
            for bindings in self._bindings_by_target.values()
            for binding in bindings
        ]

    def bindings_for_target(
        self,
        target_name: str,
    ) -> list[RenderPassBinding]:
        return list(
            self._bindings_by_target.get(
                target_name,
                (),
            )
        )

    def select_sources_for_pass(
        self,
        pass_name: str,
        *,
        include_hidden: bool = False,
    ) -> list[RenderContext]:
        selected: dict[str, RenderContext] = {}

        for link in self.links_for_pass(pass_name):
            source_contexts = self.contexts.select(
                selection=link.sources,
                include_hidden=include_hidden,
            )

            for context in source_contexts:
                selected[context.name] = context

        return list(selected.values())

    def remove_context(
        self,
        name: str,
    ) -> None:
        bindings = self._bindings_by_target.pop(
            name,
            [],
        )

        for binding in bindings:
            self._detach_binding(binding)

        for link in self._links:
            link.bindings = [
                binding
                for binding in link.bindings
                if binding.target_name != name
            ]

    def remove_render_pass(
        self,
        pass_name: str,
    ) -> None:
        for bindings in self._bindings_by_target.values():
            for binding in bindings:
                if binding.pass_name == pass_name:
                    self._detach_binding(binding)

        self._links = [
            link
            for link in self._links
            if link.pass_name != pass_name
        ]

        for target_name, bindings in list(self._bindings_by_target.items()):
            remaining = [
                binding
                for binding in bindings
                if binding.pass_name != pass_name
            ]

            if remaining:
                self._bindings_by_target[target_name] = remaining
            else:
                self._bindings_by_target.pop(
                    target_name,
                    None,
                )

    # =================================== #
    # Internals
    # =================================== #

    def _get_or_create_binding(
        self,
        *,
        pass_name: str,
        target_name: str,
        output: RenderPassOutput,
        uniform: str,
    ) -> tuple[RenderPassBinding, bool]:
        existing = self._find_binding(
            pass_name=pass_name,
            target_name=target_name,
            output=output,
            uniform=uniform,
        )

        if existing is not None:
            return existing, False

        binding = RenderPassBinding(
            pass_name=pass_name,
            target_name=target_name,
            output=output,
            uniform=uniform,
            slot=self._next_texture_slot(
                target_name=target_name,
            ),
        )

        self._bindings_by_target.setdefault(
            target_name,
            [],
        ).append(binding)

        return binding, True

    def _find_binding(
        self,
        *,
        pass_name: str,
        target_name: str,
        output: RenderPassOutput,
        uniform: str,
    ) -> RenderPassBinding | None:
        bindings = self._bindings_by_target.get(
            target_name,
            (),
        )

        for binding in bindings:
            if (
                binding.pass_name == pass_name
                and binding.output == output
                and binding.uniform == uniform
            ):
                return binding

        return None

    def _next_texture_slot(
        self,
        *,
        target_name: str,
    ) -> int:
        used_slots = {
            binding.slot
            for binding in self._bindings_by_target.get(
                target_name,
                (),
            )
        }

        slot = RENDER_PASS_TEXTURE_START_SLOT

        while slot in used_slots:
            slot += 1

        return slot

    def _find_link(
        self,
        *,
        pass_name: str,
        uniform: str,
        output: RenderPassOutput,
        sources: ContextSelection,
        targets: ContextSelection,
    ) -> RenderPassLink | None:
        for link in self._links:
            if (
                link.pass_name == pass_name
                and link.uniform == uniform
                and link.output == output
                and self._same_selection(link.sources, sources)
                and self._same_selection(link.targets, targets)
            ):
                return link

        return None

    def _same_selection(
        self,
        a: ContextSelection,
        b: ContextSelection,
    ) -> bool:
        return (
            a.names == b.names
            and a.tags == b.tags
        )


    def _detach_binding(
        self,
        binding: RenderPassBinding,
    ) -> None:
        if binding.texture_callback is None:
            return

        try:
            render_pass = self.passes.get(binding.pass_name)
        except KeyError:
            render_pass = None

        if render_pass is not None:
            render_pass.unbind(
                texture_ref=binding.texture_callback,
            )

        binding.texture_callback = None
        binding.instruction = None

    def _attach_binding(
        self,
        *,
        binding: RenderPassBinding,
        render_pass: RenderPass,
        target_context: RenderContext,
    ) -> None:
        if binding.instruction is not None:
            return

        instruction = target_context.bind_texture(
            uniform=binding.uniform,
            texture=render_pass.texture_ref,
            slot=binding.slot,
        )

        callback = partial(
            self._update_binding_texture,
            binding,
            target_context,
        )

        render_pass.bind(
            texture_ref=callback,
        )

        binding.instruction = instruction
        binding.texture_callback = callback


    def _update_binding_texture(
        self,
        binding: RenderPassBinding,
        target_context: RenderContext,
        render_pass: RenderPass,
        texture: Texture,
    ) -> None:
        if binding.instruction is None:
            return

        binding.instruction.texture = texture
        target_context.ctx.ask_update()


# =================================== #
# Context Manager Facade
# =================================== #

class RenderContextManager:
    def __init__(self) -> None:
        self.contexts = RenderContextRegistry()
        self.passes = RenderPassRegistry()

        self.binder = RenderPassBinder(
            contexts=self.contexts,
            passes=self.passes,
        )

    def __len__(self) -> int:
        return len(self.contexts)

    # =================================== #
    # General
    # =================================== #

    def get(
        self,
        name: str,
    ) -> RenderContext | RenderPass:
        if self.contexts.exists(name):
            return self.contexts.get(name)

        if self.passes.exists(name):
            return self.passes.get(name)

        raise KeyError(
            f"Render object does not exist: {name!r}"
        )

    def _ensure_name_available(
        self,
        name: str,
    ) -> None:
        if self.contexts.exists(name):
            raise ValueError(
                f"Render context already exists: {name!r}"
            )

        if self.passes.exists(name):
            raise ValueError(
                f"Render pass already exists: {name!r}"
            )

    # =================================== #
    # Contexts
    # =================================== #

    def create_context(self, name: str, **kwargs) -> RenderContext:
        self._ensure_name_available(name)
        return self.contexts.create(name=name, **kwargs)


    def destroy_context(
        self,
        name: str,
    ) -> RenderContext | None:
        context = self.contexts.remove(name)

        if context is not None:
            self.binder.remove_context(name)

        return context

    def get_context(
        self,
        name: str,
    ) -> RenderContext:
        return self.contexts.get(name)

    def context_exists(
        self,
        name: str,
    ) -> bool:
        return self.contexts.exists(name)

    def hide_context(
        self,
        name: str,
    ) -> None:
        self.contexts.hide(name)

    def show_context(
        self,
        name: str,
    ) -> None:
        self.contexts.show(name)

    def context_hidden(
        self,
        name: str,
    ) -> bool:
        return self.contexts.hidden(name)

    def context_names(
        self,
        *,
        include_hidden: bool = True,
    ) -> list[str]:
        return self.contexts.names(
            include_hidden=include_hidden,
        )

    def context_values(
        self,
        *,
        include_hidden: bool = True,
    ) -> list[RenderContext]:
        return self.contexts.values(
            include_hidden=include_hidden,
        )

    def context_items(
        self,
        *,
        include_hidden: bool = True,
    ) -> list[tuple[str, RenderContext]]:
        return self.contexts.items(
            include_hidden=include_hidden,
        )

    def select_contexts(
        self,
        *,
        tags: set[str] | None = None,
        names: set[str] | None = None,
        include_hidden: bool = True,
    ) -> list[RenderContext]:
        return self.contexts.select(
            names=names,
            tags=tags,
            include_hidden=include_hidden,
        )

    # =================================== #
    # Render Passes
    # =================================== #

    def create_render_pass(self, name: str, **kwargs) -> RenderPass:
        self._ensure_name_available(name)
        return self.passes.create(name=name, **kwargs)


    def destroy_render_pass(
        self,
        name: str,
    ) -> RenderPass | None:
        if not self.passes.exists(name):
            return None

        self.binder.remove_render_pass(name)

        return self.passes.remove(name)

    def get_render_pass(
        self,
        name: str,
    ) -> RenderPass:
        return self.passes.get(name)

    def render_pass_exists(
        self,
        name: str,
    ) -> bool:
        return self.passes.exists(name)

    def render_pass_names(self) -> list[str]:
        return self.passes.names()

    def render_pass_values(self) -> list[RenderPass]:
        return self.passes.values()

    def render_pass_items(self) -> list[tuple[str, RenderPass]]:
        return self.passes.items()

    def select_render_passes(
        self,
        *,
        tags: set[str] | None = None,
        names: set[str] | None = None,
    ) -> list[RenderPass]:
        return self.passes.select(
            names=names,
            tags=tags,
        )

    # =================================== #
    # Render Pass Links / Bindings
    # =================================== #

    def link_render_pass(self, **kwargs) -> RenderPassLink:
        return self.binder.link(**kwargs)

    def register_render_pass_link(self, **kwargs) -> RenderPassLink:
        return self.link_render_pass(**kwargs)

    def render_pass_links(self) -> list[RenderPassLink]:
        return self.binder.links()

    def get_render_pass_links(
        self,
        context_name: str,
    ) -> list[RenderPassLink]:
        return self.binder.links_for_target(
            context_name,
        )

    def get_render_pass_source_links(
        self,
        context_name: str,
    ) -> list[RenderPassLink]:
        return self.binder.links_for_source(
            context_name,
        )

    def render_pass_bindings(self) -> list[RenderPassBinding]:
        return self.binder.bindings()

    def get_render_pass_bindings(
        self,
        context_name: str,
    ) -> list[RenderPassBinding]:
        return self.binder.bindings_for_target(
            context_name,
        )

    def select_render_pass_sources(
        self,
        pass_name: str,
        *,
        include_hidden: bool = False,
    ) -> list[RenderContext]:
        return self.binder.select_sources_for_pass(
            pass_name,
            include_hidden=include_hidden,
        )

    # =================================== #
    # Context Tags
    # =================================== #

    def add_context_tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        self.contexts.add_tag(
            name,
            tag,
        )

    def remove_context_tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        self.contexts.remove_tag(
            name,
            tag,
        )

    def get_context_tags(
        self,
        name: str,
    ) -> set[str]:
        return self.contexts.get_tags(name)

    # =================================== #
    # Render Pass Tags
    # =================================== #

    def add_render_pass_tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        self.passes.add_tag(
            name,
            tag,
        )

    def remove_render_pass_tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        self.passes.remove_tag(
            name,
            tag,
        )

    def get_render_pass_tags(
        self,
        name: str,
    ) -> set[str]:
        return self.passes.get_tags(name)

    # =================================== #
    # Context Uniforms
    # =================================== #

    def set_context_uniform(
        self,
        name: str,
        uniform: str,
        value,
    ) -> None:
        self.contexts.set_uniform(
            name,
            uniform,
            value,
        )

    def set_context_uniform_by_tag(
        self,
        tag: str,
        uniform: str,
        value,
        *,
        include_hidden: bool = True,
    ) -> None:
        self.contexts.set_uniform_by_tag(
            tag,
            uniform,
            value,
            include_hidden=include_hidden,
        )

    # =================================== #
    # Render Pass Uniforms
    # =================================== #

    def set_render_pass_uniform(
        self,
        name: str,
        uniform: str,
        value,
    ) -> None:
        self.passes.set_uniform(
            name,
            uniform,
            value,
        )

    def set_render_pass_uniform_by_tag(
        self,
        tag: str,
        uniform: str,
        value,
    ) -> None:
        self.passes.set_uniform_by_tag(
            tag,
            uniform,
            value,
        )

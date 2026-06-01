# kivyfn/three/render/context_registry.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from kivyfn.three.render.context import (
    RenderContext,
    RenderPass,
)

TContext = TypeVar(
    "TContext",
    RenderContext,
    RenderPass,
)


# =================================== #
# Selection
# =================================== #

@dataclass(slots=True)
class ContextSelection:
    names: set[str] | None = None
    tags: set[str] | None = None


# =================================== #
# Managed Object
# =================================== #

@dataclass(slots=True)
class ManagedRenderObject(Generic[TContext]):
    name: str
    context: TContext
    tags: set[str] = field(default_factory=set)


# =================================== #
# Base Registry
# =================================== #

class RenderObjectRegistry(Generic[TContext]):
    def __init__(
        self,
        *,
        label: str,
    ) -> None:
        self.label = label
        self._items: dict[str, ManagedRenderObject[TContext]] = {}

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(
        self,
        name: str,
    ) -> bool:
        return name in self._items

    # =================================== #
    # CRUD
    # =================================== #

    def add(
        self,
        name: str,
        context: TContext,
        *,
        tags: set[str] | None = None,
    ) -> TContext:
        if name in self._items:
            raise ValueError(
                f"{self.label} already exists: {name!r}"
            )

        self._items[name] = ManagedRenderObject(
            name=name,
            context=context,
            tags=set(tags or ()),
        )

        return context

    def remove(
        self,
        name: str,
    ) -> TContext | None:
        managed = self._items.pop(
            name,
            None,
        )

        if managed is None:
            return None

        return managed.context

    def get(
        self,
        name: str,
    ) -> TContext:
        try:
            return self._items[name].context
        except KeyError:
            raise KeyError(
                f"{self.label} does not exist: {name!r}"
            ) from None

    def exists(
        self,
        name: str,
    ) -> bool:
        return name in self._items

    # =================================== #
    # Iteration
    # =================================== #

    def names(self) -> list[str]:
        return list(self._items.keys())

    def values(self) -> list[TContext]:
        return [
            managed.context
            for managed in self._items.values()
        ]

    def items(self) -> list[tuple[str, TContext]]:
        return [
            (
                name,
                managed.context,
            )
            for name, managed in self._items.items()
        ]

    # =================================== #
    # Selection
    # =================================== #

    def _select(
        self,
        *,
        selection: ContextSelection | None = None,
        names: set[str] | None = None,
        tags: set[str] | None = None,
        hidden: set[str] | None = None,
        include_hidden: bool = True,
    ) -> list[TContext]:
        if selection is not None:
            names = selection.names
            tags = selection.tags

        selected: list[TContext] = []

        for name, managed in self._items.items():
            if (
                hidden is not None
                and not include_hidden
                and name in hidden
            ):
                continue

            if names is not None and name not in names:
                continue

            if tags is not None and not tags.intersection(managed.tags):
                continue

            selected.append(managed.context)

        return selected

    # =================================== #
    # Tags
    # =================================== #

    def add_tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        self._items[name].tags.add(tag)

    def remove_tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        self._items[name].tags.discard(tag)

    def get_tags(
        self,
        name: str,
    ) -> set[str]:
        return set(self._items[name].tags)

    # =================================== #
    # Uniforms
    # =================================== #

    def set_uniform(
        self,
        name: str,
        uniform: str,
        value,
    ) -> None:
        self.get(name).set_uniform(
            uniform,
            value,
        )

    def _set_uniform_by_tag(
        self,
        tag: str,
        uniform: str,
        value,
        *,
        hidden: set[str] | None = None,
        include_hidden: bool = True,
    ) -> None:
        for name, managed in self._items.items():
            if (
                hidden is not None
                and not include_hidden
                and name in hidden
            ):
                continue

            if tag not in managed.tags:
                continue

            managed.context.set_uniform(
                uniform,
                value,
            )


# =================================== #
# Render Context Registry
# =================================== #

class RenderContextRegistry(RenderObjectRegistry[RenderContext]):
    def __init__(self) -> None:
        super().__init__(
            label="Render context",
        )

        self._hidden: set[str] = set()

    # =================================== #
    # Creation
    # =================================== #

    def create(self, name: str, tags: set[str] | None, **kwargs) -> RenderContext:
        context = RenderContext(name=name, **kwargs)
        return self.add(
            name,
            context,
            tags=tags,
        )

    def remove(
        self,
        name: str,
    ) -> RenderContext | None:
        context = super().remove(name)

        self._hidden.discard(name)

        return context

    # =================================== #
    # Visibility
    # =================================== #

    def hide(
        self,
        name: str,
    ) -> None:
        if name not in self:
            raise KeyError(
                f"Render context does not exist: {name!r}"
            )

        self._hidden.add(name)

    def show(
        self,
        name: str,
    ) -> None:
        if name not in self:
            raise KeyError(
                f"Render context does not exist: {name!r}"
            )

        self._hidden.discard(name)

    def hidden(
        self,
        name: str,
    ) -> bool:
        return name in self._hidden

    # =================================== #
    # Iteration
    # =================================== #

    def names(
        self,
        *,
        include_hidden: bool = True,
    ) -> list[str]:
        return [
            name
            for name in self._items
            if include_hidden or name not in self._hidden
        ]

    def values(
        self,
        *,
        include_hidden: bool = True,
    ) -> list[RenderContext]:
        return [
            managed.context
            for name, managed in self._items.items()
            if include_hidden or name not in self._hidden
        ]

    def items(
        self,
        *,
        include_hidden: bool = True,
    ) -> list[tuple[str, RenderContext]]:
        return [
            (
                name,
                managed.context,
            )
            for name, managed in self._items.items()
            if include_hidden or name not in self._hidden
        ]

    # =================================== #
    # Selection
    # =================================== #

    def select(
        self,
        *,
        selection: ContextSelection | None = None,
        names: set[str] | None = None,
        tags: set[str] | None = None,
        include_hidden: bool = True,
    ) -> list[RenderContext]:
        return self._select(
            selection=selection,
            names=names,
            tags=tags,
            hidden=self._hidden,
            include_hidden=include_hidden,
        )

    # =================================== #
    # Uniforms
    # =================================== #

    def set_uniform_by_tag(
        self,
        tag: str,
        uniform: str,
        value,
        *,
        include_hidden: bool = True,
    ) -> None:
        self._set_uniform_by_tag(
            tag,
            uniform,
            value,
            hidden=self._hidden,
            include_hidden=include_hidden,
        )


# =================================== #
# Render Pass Registry
# =================================== #

class RenderPassRegistry(RenderObjectRegistry[RenderPass]):
    def __init__(self) -> None:
        super().__init__(
            label="Render pass",
        )

    # =================================== #
    # Creation
    # =================================== #

    def create(self, name: str, tags: set[str] | None, **kwargs) -> RenderPass:
        render_pass = RenderPass(name=name, **kwargs)
        return self.add(
            name,
            render_pass,
            tags=tags,
        )

    # =================================== #
    # Selection
    # =================================== #

    def select(
        self,
        *,
        selection: ContextSelection | None = None,
        names: set[str] | None = None,
        tags: set[str] | None = None,
    ) -> list[RenderPass]:
        return self._select(
            selection=selection,
            names=names,
            tags=tags,
            include_hidden=True,
        )

    # =================================== #
    # Uniforms
    # =================================== #

    def set_uniform_by_tag(
        self,
        tag: str,
        uniform: str,
        value,
    ) -> None:
        self._set_uniform_by_tag(
            tag,
            uniform,
            value,
        )

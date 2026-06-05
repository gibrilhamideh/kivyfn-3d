# kivyfn/three/render/stage_registry.py
from __future__ import annotations

from collections import defaultdict
from typing import NoReturn

from kivyfn.three.types import RenderStage
from kivyfn.three.render.context import RenderContext, RenderPass


class RenderStageRegistry:

    def __len__(self) -> int:
        return (
            len(self._contexts) +
            len(self._passes)
        )

    def __init__(self) -> None:
        self._contexts: dict[str, RenderContext] = {}
        self._passes: dict[str, RenderPass] = {}

        self._tags: defaultdict[str, set[str]] = defaultdict(set)
        """
        Maps tag names to render stage names.

        Example:
        {
            "main-tag": {"main-context", "ui-context"},
            "shadow-tag": {"shadow-pass"},
        }
        """

    # =================================== #
    # Exports
    # =================================== #
    @property
    def contexts(self) -> dict[str, RenderContext]:
        return self._contexts.copy()


    @property
    def passes(self) -> dict[str, RenderPass]:
        return self._passes.copy()

    # =================================== #
    # Context Registrations
    # =================================== #

    def add(
        self,
        ctx: RenderStage,
    ) -> None:
        name = ctx.name

        if name in self._contexts or name in self._passes:
            raise ValueError(
                f"Render stage '{name}' is already registered."
            )

        if isinstance(ctx, RenderPass):
            self._passes[name] = ctx
        else:
            self._contexts[name] = ctx

    def remove(
        self,
        name: str,
    ) -> RenderStage:
        stage = self.require(name)

        if isinstance(stage, RenderPass):
            del self._passes[name]
        else:
            del self._contexts[name]

        return stage

    def exists(
        self,
        name: str,
    ) -> bool:
        return self.get(name) is not None

    def get(
        self,
        name: str,
    ) -> RenderStage | None:
        context = self._contexts.get(name)
        if context is not None:
            return context

        return self._passes.get(name)

    def get_context(
        self,
        name: str,
    ) -> RenderContext | None:
        return self._contexts.get(name)

    def get_pass(
        self,
        name: str,
    ) -> RenderPass | None:
        return self._passes.get(name)

    def require(
        self,
        name: str,
    ) -> RenderStage | NoReturn:
        context = self._contexts.get(name)
        if context is not None:
            return context

        render_pass = self._passes.get(name)
        if render_pass is not None:
            return render_pass

        raise KeyError(
            f"Render stage '{name}' is not registered."
        )

    def require_context(
        self,
        name: str,
    ) -> RenderContext:
        stage = self.require(name)

        if not isinstance(stage, RenderContext):
            raise TypeError(
                f"Render stage '{name}' is not a RenderContext."
            )

        return stage

    def require_pass(
        self,
        name: str,
    ) -> RenderPass:
        stage = self.require(name)

        if not isinstance(stage, RenderPass):
            raise TypeError(
                f"Render stage '{name}' is not a RenderPass."
            )

        return stage

    # =================================== #
    # Tag Registrations
    # =================================== #

    def add_tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        self._tags[tag].add(name)

    def remove_tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        names = self._tags.get(tag)
        if names is None:
            return

        names.discard(name)

        if not names:
            del self._tags[tag]


    def get_by_tag(
        self,
        tag: str,
    ) -> list[RenderStage]:
        names = self._tags.get(tag)
        if names is None:
            return []

        return [
            stage
            for name in names
            if (stage := self.get(name)) is not None
        ]

    def require_by_tag(
        self,
        tag: str,
    ) -> list[RenderStage] | NoReturn:
        stages = self.get_by_tag(tag)

        if not stages:
            raise KeyError(
                f"No render stages found with tag '{tag}'."
            )

        return stages

    def tags_of(
        self,
        name: str,
    ) -> set[str]:
        return {
            tag
            for tag, names in self._tags.items()
            if name in names
        }

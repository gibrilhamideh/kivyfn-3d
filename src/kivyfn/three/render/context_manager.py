# kivyfn/three/render/context_manager.py

from __future__ import annotations

from kivyfn.three.types import RenderStage
from kivyfn.three.render.context import (
    RenderContext,
    RenderPass,
)
from kivyfn.three.render.context_registry import RenderRegistry
from kivyfn.three.render.link_registry import (
    RenderLinkRecord,
    RenderLinkRegistry,
)
from kivyfn.three.render.binding_registry import (
    RenderBindingRecord,
    RenderBindingRegistry,
)
from kivyfn.three.render.binder_manager import (
    RenderBinderManager,
)


class RenderContextManager:

    def __init__(self) -> None:
        self.registry = RenderRegistry()

        self.links = RenderLinkRegistry(
            registry=self.registry,
        )

        self.bindings = RenderBindingRegistry(
            registry=self.registry,
        )

        self.binder_manager = RenderBinderManager(
            context_registry=self.registry,
            binder_registry=self.bindings,
        )

        self.hidden = {}

    def __len__(self) -> int:
        return len(self.registry)

    # =================================== #
    # General API
    # =================================== #

    def add(
        self,
        stage: RenderStage,
    ) -> RenderStage:
        self.registry.add(stage)
        return stage

    def get(
        self,
        name: str,
    ) -> RenderStage | None:
        return self.registry.get(name)

    def require(
        self,
        name: str,
    ) -> RenderStage:
        return self.registry.require(name)

    def exists(
        self,
        name: str,
    ) -> bool:
        return self.registry.get(name) is not None

    def remove(
        self,
        name: str,
    ) -> RenderStage:
        self.registry.require(name)

        self.links.require_no_dependents(name)
        self.bindings.require_no_dependents(name)

        return self.registry.remove(name)


    def destroy(
        self,
        name: str,
    ) -> list[RenderStage]:
        """
        Recursively destroys a render stage and all stages that
        depend on it.

        Example:

            shadow-pass -> main-context -> ui-context

            destroy("shadow-pass")

        Removes:

            ui-context
            main-context
            shadow-pass
        """
        self.registry.require(name)

        destroyed: list[RenderStage] = []
        visited: set[str] = set()

        def walk(stage_name: str) -> None:
            if stage_name in visited:
                return

            visited.add(stage_name)

            for dependent in self.dependents(stage_name):
                walk(dependent)

            link_records = set(self.links.outgoing(stage_name) or ())
            link_records |= set(self.links.incoming(stage_name) or ())

            for record in link_records:
                self.links.unlink(record)

            binder_records = set(self.bindings.outgoing(stage_name) or ())
            binder_records |= set(self.bindings.incoming(stage_name) or ())

            for record in binder_records:
                self.binder_manager.detach(record)
                self.bindings.remove(record)

            destroyed.append(
                self.registry.remove(stage_name)
            )

        walk(name)

        return destroyed


    # =================================== #
    # Context API
    # =================================== #

    def create_context(
        self,
        name: str,
        tags: set[str] | None,
        **kwargs,
    ) -> RenderContext:

        context = RenderContext(
            name=name,
            **kwargs,
        )

        if tags is not None:
            for tag in tags:
                self.tag(name, tag)

        self.add(context)

        return context

    def require_context(
        self,
        name: str,
    ) -> RenderContext:
        return self.registry.require_context(name)

    def get_context(
        self,
        name: str,
    ) -> RenderContext | None:
        return self.registry.get_context(name)

    def remove_context(
        self,
        name: str,
    ) -> RenderContext:
        stage = self.remove(name)

        if not isinstance(stage, RenderContext):
            raise TypeError(
                f"Render stage '{name}' is not a RenderContext."
            )

        return stage

    # =================================== #
    # Render Pass API
    # =================================== #

    def create_pass(
        self,
        name: str,
        tags: set[str] | None,
        **kwargs,
    ) -> RenderPass:
        render_pass = RenderPass(
            name=name,
            **kwargs,
        )

        if tags is not None:
            for tag in tags:
                self.tag(name, tag)

        self.add(render_pass)

        return render_pass

    def require_pass(
        self,
        name: str,
    ) -> RenderPass:
        stage = self.registry.require(name)

        if not isinstance(stage, RenderPass):
            raise TypeError(
                f"Render stage '{name}' is not a RenderPass."
            )

        return stage

    def get_pass(
        self,
        name: str,
    ) -> RenderPass | None:
        return self.registry.get_pass(name)

    def remove_pass(
        self,
        name: str,
    ) -> RenderPass:
        stage = self.remove(
            name,
        )

        if not isinstance(stage, RenderPass):
            raise TypeError(
                f"Render stage '{name}' is not a RenderPass."
            )

        return stage

    def attach_pass(
        self,
        *,
        pass_name: str,
        target_name: str | None = None,
        target_tags: set[str] | None = None,
        index: int | None = None,
    ) -> RenderBindingRecord | list[RenderBindingRecord]:
        if target_name is None and not target_tags:
            raise ValueError(
                "attach_pass() requires either 'target_name' or 'target_tags'."
            )

        if target_name is not None and target_tags:
            raise ValueError(
                "attach_pass() accepts either 'target_name' or 'target_tags', not both."
            )

        if target_name is not None:
            return self.binder_manager.attach(
                pass_name=pass_name,
                target_name=target_name,
                index=index,
            )

        if index is not None:
            raise ValueError(
                "attach_pass() cannot use a fixed texture index when attaching "
                "to multiple targets by tag."
            )

        targets = self.select_contexts(
            tags=target_tags,
        )

        return [
            self.binder_manager.attach(
                pass_name=pass_name,
                target_name=target.name,
            )
            for target in targets
        ]

    # =================================== #
    # Tags API
    # =================================== #

    def tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        self.registry.add_tag(name, tag)

    def untag(
        self,
        name: str,
        tag: str,
    ) -> None:
        self.registry.remove_tag(name, tag)

    def get_by_tag(
        self,
        tag: str,
    ) -> list[RenderStage]:
        return self.registry.get_by_tag(tag)

    def require_by_tag(
        self,
        tag: str,
    ) -> list[RenderStage]:
        return self.registry.require_by_tag(tag)

    # =================================== #
    # Selection API
    # =================================== #

    def select(
        self,
        *,
        tags: set[str] | None = None,
    ) -> list[RenderStage]:
        selected: dict[str, RenderStage] = {}

        for tag in tags or ():
            for stage in self.registry.get_by_tag(tag):
                selected[stage.name] = stage

        return list(selected.values())

    def select_contexts(
        self,
        *,
        tags: set[str] | None = None,
    ) -> list[RenderContext]:
        return [
            stage
            for stage in self.select(
                tags=tags,
            )
            if isinstance(stage, RenderContext)
        ]

    def select_passes(
        self,
        *,
        tags: set[str] | None = None,
    ) -> list[RenderPass]:
        return [
            stage
            for stage in self.select(
                tags=tags,
            )
            if isinstance(stage, RenderPass)
        ]

    # =================================== #
    # Link API
    # =================================== #
    def link(
        self,
        source: str,
        *,
        target_name: str | None = None,
        target_tags: set[str] | None = None,
    ) -> RenderLinkRecord | list[RenderLinkRecord]:
        if target_name is None and not target_tags:
            raise ValueError(
                "link() requires either 'target_name' or 'target_tags'."
            )

        if target_name is not None and target_tags:
            raise ValueError(
                "link() accepts either 'target_name' or 'target_tags', not both."
            )

        if target_name is not None:
            return self.links.add(
                source=source,
                target=target_name,
            )

        targets = self.select(
            tags=target_tags,
        )

        return [
            self.links.add(
                source=source,
                target=target.name,
            )
            for target in targets
        ]

    def unlink(
        self,
        *,
        source: str,
        target_name: str | None = None,
        target_tags: set[str] | None = None,
    ) -> RenderLinkRecord | list[RenderLinkRecord]:
        if target_name is None and not target_tags:
            raise ValueError(
                "unlink() requires either 'target_name' or 'target_tags'."
            )

        if target_name is not None and target_tags:
            raise ValueError(
                "unlink() accepts either 'target_name' or 'target_tags', not both."
            )

        if target_name is not None:
            return self.links.remove(
                source=source,
                target=target_name,
            )

        targets = self.select(
            tags=target_tags,
        )

        return [
            self.links.remove(
                source=source,
                target=target.name,
            )
            for target in targets
        ]

    def unlink_by_source(
        self,
        source: str,
    ) -> set[RenderLinkRecord]:
        return self.links.unlink_by_source(source)

    def unlink_by_target(
        self,
        target: str,
    ) -> set[RenderLinkRecord]:
        return self.links.unlink_by_target(target)


    # =================================== #
    # Dependency API
    # =================================== #

    def dependencies(
        self,
        target: str,
    ) -> set[str]:
        linked = self.links.dependencies(target)
        bound = self.bindings.dependencies(target)

        return set(linked or ()) | set(bound or ())

    def dependents(
        self,
        source: str,
    ) -> set[str]:
        linked = self.links.dependents(source)
        bound = self.bindings.dependents(source)

        return set(linked or ()) | set(bound or ())


    # =================================== #
    # Uniform API
    # =================================== #

    def set_uniform(
        self,
        name: str,
        uniform: str,
        value,
    ) -> None:
        stage = self.registry.require(name)
        stage[uniform] = value

    def set_uniform_by_tag(
        self,
        tag: str,
        uniform: str,
        value,
    ) -> None:
        for stage in self.registry.get_by_tag(tag):
            stage[uniform] = value

    # =================================== #
    # Internals
    # =================================== #

    def _format_names(
        self,
        names: set[str] | None,
    ) -> str:
        if not names:
            return "none"

        return ", ".join(sorted(names))

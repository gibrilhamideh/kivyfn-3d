# kivyfn/three/render/context_manager.py

from __future__ import annotations

from kivyfn.three.types import (
    RenderStage,
    RenderStageName,
    RenderPassName,
    RenderContextName,
)

from kivyfn.three.render.context import (
    RenderContext,
    RenderPass,
)

from kivyfn.three.render.registry import RenderStageRegistry

from kivyfn.three.render.binder import (
    RenderBindingRecord,
    RenderBindingRegistry,
    RenderBinderManager,
)


class RenderStageManager:

    def __init__(self) -> None:
        self.registry = RenderStageRegistry()

        self.bindings = RenderBindingRegistry(
            registry=self.registry,
        )

        self.binder_manager = RenderBinderManager(
            stage_registry=self.registry,
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
        self.registry.register(stage)
        return stage

    def remove(
        self,
        name: RenderStageName,
    ) -> RenderStage:
        self.registry.require(name)

        self.bindings.require_no_dependents(name)
        return self.registry.unregister(name)

    def destroy(
        self,
        name: RenderStageName,
    ) -> list[RenderStage]:
        """
        Recursively destroys a render stage and stages that depend on its output bindings.

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

            binder_records = set(self.bindings.outgoing(stage_name) or ())
            binder_records |= set(self.bindings.incoming(stage_name) or ())

            for record in binder_records:
                self.binder_manager.detach(record)
                self.bindings.remove(record)

            destroyed.append(
                self.registry.unregister(stage_name)
            )

        walk(name)

        return destroyed


    # =================================== #
    # Context API
    # =================================== #

    def create_context(
        self,
        name: RenderContextName,
        tags: set[str] | None,
        **kwargs,
    ) -> RenderContext:

        context = RenderContext(
            name=name,
            **kwargs,
        )

        self.add(context)
        if tags is not None:
            for tag in tags:
                self.registry.tag(name, tag)

        return context


    def remove_context(
        self,
        name: RenderContextName,
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
        name: RenderPassName,
        tags: set[str] | None,
        **kwargs,
    ) -> RenderPass:
        render_pass = RenderPass(
            name=name,
            **kwargs,
        )

        self.add(render_pass)
        if tags is not None:
            for tag in tags:
                self.registry.tag(name, tag)

        return render_pass


    def remove_pass(
        self,
        name: RenderPassName,
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
        name: RenderPassName,
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
                pass_name=name,
                target_name=target_name,
                index=index,
            )

        if index is not None:
            raise ValueError(
                "attach_pass() cannot use a fixed texture index when attaching "
                "to multiple targets by tag."
            )

        assert target_tags is not None

        targets: dict[str, RenderContext] = {}

        for tag in target_tags:
            for target in self.registry.contexts_of(tag):
                targets[target.name] = target

        return [
            self.binder_manager.attach(
                pass_name=name,
                target_name=target.name,
            )
            for target in targets.values()
        ]



    # =================================== #
    # Dependency API
    # =================================== #

    def dependencies(
        self,
        target: str,
    ) -> set[str]:
        bound = self.bindings.dependencies(target)

        return set(bound or ())

    def dependents(
        self,
        source: str,
    ) -> set[str]:
        bound = self.bindings.dependents(source)

        return set(bound or ())


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
        for stage in self.registry.stages_of(tag):
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

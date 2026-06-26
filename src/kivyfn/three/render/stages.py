# kivyfn/three/render/context_manager.py

from __future__ import annotations

from kivyfn.three.types import RenderStage

from kivyfn.three.render.context import (
    RenderContext,
    RenderPass2D,
    RenderPassCube,
)

from kivyfn.three.render.registry import RenderStageRegistry

from kivyfn.three.render.binder import (
    RenderBindingRecord,
    RenderBindingRegistry,
    RenderBinderManager,
    RenderBindingGraph
)


class RenderStageManager:

    def __init__(self) -> None:
        self.registry = RenderStageRegistry()

        self.bindings = RenderBindingRegistry(
            registry=self.registry,
        )

        self.binder_manager = RenderBinderManager(
            stage_registry=self.registry,
            binding_registry=self.bindings,
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
        name: str,
    ) -> RenderStage:
        self.registry.require(name)

        graph = self.removal_plan(name)
        if graph.dependents:
            dependents = ", ".join(graph.dependents)

            raise RuntimeError(
                f"Cannot remove render stage {name!r} because it is "
                f"required by: {dependents}."
            )

        for record in list(self.bindings.incoming(name) or ()):
            self.binder_manager.detach(record)
            self.bindings.remove(record)

        return self.registry.unregister(name)

    def removal_plan(
        self,
        name: str,
    ) -> RenderBindingGraph:
        return self.bindings.graph_of(name)


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

        self.add(context)
        if tags is not None:
            for tag in tags:
                self.registry.tag(name, tag)

        return context


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
    ) -> RenderPass2D:
        render_pass = RenderPass2D(
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
        name: str,
    ) -> RenderPass2D:
        stage = self.remove(name)

        if not isinstance(stage, RenderPass2D):
            raise TypeError(
                f"Render stage '{name}' is not a RenderPass."
            )

        return stage

    # =================================== #
    # Cube Render Pass API
    # =================================== #
    def create_cube_pass(
        self,
        name: str,
        tags: set[str] | None,
        **kwargs,
    ) -> RenderPassCube:
        cube_pass = RenderPassCube(
            name=name,
            **kwargs,
        )

        self.add(cube_pass)

        if tags is not None:
            for tag in tags:
                self.registry.tag(name, tag)

        return cube_pass

    def remove_cube_pass(
        self,
        name: str,
    ) -> RenderPassCube:
        stage = self.remove(name)

        if not isinstance(stage, RenderPassCube):
            raise TypeError(
                f"Render stage '{name}' is not a CubeRenderPass."
            )

        return stage

    # =================================== #
    # Pass Attachment
    # =================================== #
    def attach_pass(
        self,
        *,
        name: str,
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

    def dependencies_of(
        self,
        name: str,
    ) -> set[str]:
        bound = self.bindings.dependencies_of(name)

        return set(bound or ())

    def dependents_of(
        self,
        name: str,
    ) -> set[str]:
        bound = self.bindings.dependents_of(name)

        return set(bound or ())

    def graph_of(
        self,
        name: str,
    ) -> RenderBindingGraph:
        return self.bindings.graph_of(name)


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

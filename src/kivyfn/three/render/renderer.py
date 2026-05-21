# kivyfn/three/render/renderer.py

from __future__ import annotations

from functools import partial
from typing import Callable

from kivy.graphics.transformation import Matrix
from kivy.graphics import (
    Callback,
    Canvas,
    PopMatrix,
    PushMatrix,
    Rotate,
    Scale,
    Translate,
    UpdateNormalMatrix,
)

from kivyfn.three.render.material import Material
from kivyfn.three.render.mesh import RenderMesh
from kivyfn.three.render.render_pass import RenderPass
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene.object3d import Object3D
from kivyfn.three.scene.node import Node3D


class Renderer:
    def __init__(
        self,
        canvas: Canvas,
    ):
        self.canvas = canvas

        self.passes: dict[Shader, RenderPass] = {}
        self.buckets: dict[Shader, set[Object3D]] = {}
        self.objects: set[Object3D] = set()

        self._modelview_mat: Matrix | None = None
        self._projection_mat: Matrix | None = None

    def __repr__(self) -> str:
        return f"Renderer(passes={len(self.passes)})"

    # =================================== #
    # Passes
    # =================================== #
    def clear(self) -> None:
        for render_pass in self.passes.values():
            render_pass.clear()

    def register_object(self, obj: Object3D) -> None:
        if obj in self.objects:
            return

        if obj.mesh_data is None or obj.material is None:
            return

        shader = obj.material.shader

        self.objects.add(obj)
        self.buckets.setdefault(shader, set()).add(obj)
        self.get_pass(shader)


    def unregister_object(self, obj: Object3D) -> None:
        self.objects.discard(obj)

        for shader, bucket in list(self.buckets.items()):
            bucket.discard(obj)

            if not bucket:
                self.buckets.pop(shader, None)


    def rebucket_object(self, obj: Object3D) -> None:
        self.unregister_object(obj)
        self.register_object(obj)


    def get_pass(
        self,
        shader: Shader,
    ) -> RenderPass:
        if shader in self.passes:
            return self.passes[shader]

        render_pass = RenderPass(shader)
        self.passes[shader] = render_pass
        self.canvas.add(render_pass.context)

        return render_pass

    # =================================== #
    # Render
    # =================================== #
    def build(
        self,
        root: Node3D,
        setup_gl_context: Callable,
        reset_gl_context: Callable,
    ) -> None:
        for shader in list(self.buckets.keys()):
            render_pass = self.get_pass(shader)

            with render_pass.context:
                Callback(setup_gl_context)
                self._build(root, render_pass)
                Callback(reset_gl_context)

    def _build(
        self,
        node: Node3D,
        render_pass: RenderPass,
    ) -> None:
        if not node.visible:
            return

        PushMatrix()
        self._apply_transform(node)

        node.render(self, render_pass)
        for child in node.children:
            self._build(child, render_pass)

        PopMatrix()

    def build_object(
        self,
        object3d: Object3D,
        render_pass: RenderPass,
    ) -> None:
        if object3d.mesh_data is None:
            return

        material: Material = object3d.material
        shader: Shader = material.shader

        if self.get_pass(shader) is not render_pass:
            return

        Callback(partial(self._apply_material, material, render_pass))

        if object3d.render_mesh is None:
            object3d.render_mesh = RenderMesh(
                mesh_data=object3d.mesh_data,
                mode=object3d.render_mode,
            )
        else:
            object3d.render_mesh.update_mesh_data(object3d.mesh_data)

        render_pass.context.add(object3d.render_mesh.instruction)

    # =================================== #
    # Material
    # =================================== #
    def _apply_material(
        self,
        material: Material,
        render_pass: RenderPass,
        *args,
    ) -> None:
        material.apply_to(render_pass.context)

    # =================================== #
    # Transform
    # =================================== #
    def _apply_transform(
        self,
        node: Node3D,
    ) -> None:
        transform = node.transform

        tx, ty, tz = transform.translation
        sx, sy, sz = transform.scale

        rotation = transform.rotation

        axis_x, axis_y, axis_z, angle = rotation.to_axis_angle()

        Translate(tx, ty, tz)
        Rotate(angle=angle, axis=(axis_x, axis_y, axis_z))
        Scale(sx, sy, sz)

        UpdateNormalMatrix()

    # =================================== #
    # View
    # =================================== #
    def update_view(
        self,
        camera,
        aspect: float,
    ) -> None:
        self._projection_mat = camera.get_projection_matrix(aspect)
        self._modelview_mat = camera.get_view_matrix()

        for render_pass in self.passes.values():
            render_pass.update_view(camera, aspect)

    @property
    def modelview_mat(self):
        assert self._modelview_mat is not None
        return self._modelview_mat

    @property
    def projection_mat(self):
        assert self._projection_mat is not None
        return self._projection_mat

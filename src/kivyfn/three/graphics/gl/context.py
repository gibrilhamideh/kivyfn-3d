# kivyfn/three/graphics/gl/context.py

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kivy.graphics import InstructionGroup, Callback
from kivy.graphics.context_instructions import ChangeState
from kivyfn.three.graphics.gl.core import GL
from kivyfn.three.math.matrix import Matrix3, Matrix4

if TYPE_CHECKING:
    from kivyfn.three.assets.material import Material as AssetMaterial
    from kivyfn.three.graphics.gl.texture import Texture2D, TextureCube


__all__ = (
    "BindUniform",
    "BindTransform",
    "BindGeometry",
    "BindMaterial",
    "BindObjectId",
    "BindTexture",
)


# =================================== #
# Bind Uniform
# =================================== #


class BindUniform(ChangeState):
    """
    Bind one uniform/state value to the active RenderContext.

    This is the basic per-object context instruction.
    It does not need RenderStage.
    """

    def __init__(
        self,
        name: str,
        value: Any,
        **kwargs: Any,
    ) -> None:
        self.name = name

        super().__init__(
            **{
                name: value,
            },
            **kwargs,
        )

    def sync(
        self,
        value: Any,
    ) -> None:
        self.changes = {
            self.name: value,
        }

        self.flag_data_update()


# =================================== #
# Bind Transform
# =================================== #


class BindTransform(InstructionGroup):
    def __init__(
        self,
        *,
        model_mat: Matrix4 | None = None,
        normal_mat: Matrix3 | None = None,
    ) -> None:
        super().__init__()

        self.model_mat = BindUniform(
            "model_mat",
            (model_mat or Matrix4.identity()).to_uniform(),
        )

        self.normal_mat = BindUniform(
            "normal_mat",
            (normal_mat or Matrix3.identity()).to_uniform(),
        )

        self.add(self.model_mat)
        self.add(self.normal_mat)

    def sync(
        self,
        *,
        model_mat: Matrix4,
        normal_mat: Matrix3,
    ) -> None:
        self.model_mat.sync(
            model_mat.to_uniform(),
        )

        self.normal_mat.sync(
            normal_mat.to_uniform(),
        )


# =================================== #
# Bind Geometry
# =================================== #


class BindGeometry(InstructionGroup):
    def __init__(
        self,
        *,
        has_tangents: bool,
    ) -> None:
        super().__init__()

        self.has_tangents = BindUniform(
            "has_tangents",
            self._encode_bool(has_tangents),
        )

        self.add(self.has_tangents)

    @staticmethod
    def _encode_bool(
        value: bool,
    ) -> int:
        return 1 if value else 0

    def sync(
        self,
        *,
        has_tangents: bool,
    ) -> None:
        self.has_tangents.sync(
            self._encode_bool(has_tangents),
        )


# =================================== #
# Bind Material
# =================================== #


class BindMaterial(InstructionGroup):
    def __init__(
        self,
        *,
        material: AssetMaterial,
    ) -> None:
        super().__init__()

        self.material = material
        self.uniforms: dict[str, BindUniform] = {}

        self.sync(
            material=material,
        )

    def sync(
        self,
        *,
        material: AssetMaterial | None = None,
    ) -> None:
        if material is not None:
            self.material = material

        wanted = {
            name: value
            for name, value in self.material.uniforms.items()
            if value is not None
        }

        for name in list(self.uniforms):
            if name not in wanted:
                uniform = self.uniforms.pop(name)
                self.remove(uniform)

        for name, value in wanted.items():
            uniform = self.uniforms.get(name)

            if uniform is None:
                uniform = BindUniform(
                    name,
                    value,
                )

                self.uniforms[name] = uniform
                self.add(uniform)

                continue

            uniform.sync(value)

    def set_material(
        self,
        material: AssetMaterial,
    ) -> None:
        self.sync(
            material=material,
        )


# =================================== #
# Bind Object ID
# =================================== #


class BindObjectId(InstructionGroup):
    def __init__(
        self,
        *,
        render_id: int,
        uniform: str,
    ) -> None:
        super().__init__()

        self.render_id = render_id
        self.uniform = uniform

        self.state = BindUniform(
            uniform,
            self.encode(render_id),
        )

        self.add(self.state)

    @staticmethod
    def encode(
        render_id: int,
    ) -> list[float]:
        r = (render_id >> 16) & 0xFF
        g = (render_id >> 8) & 0xFF
        b = render_id & 0xFF

        return [
            r / 255.0,
            g / 255.0,
            b / 255.0,
            1.0,
        ]

    def sync(
        self,
        *,
        render_id: int | None = None,
    ) -> None:
        if render_id is not None:
            self.render_id = render_id

        self.state.sync(
            self.encode(self.render_id),
        )


# =================================== #
# Bind Texture
# =================================== #

class BindTextureCallback(Callback):
    def __init__(
        self,
        *,
        texture: Texture2D | TextureCube,
        slot: int,
        **kwargs: Any,
    ) -> None:
        self.texture = texture
        self.slot = int(slot)

        super().__init__(
            self.apply,
            **kwargs,
        )

    def sync(
        self,
        *,
        texture: Texture2D | TextureCube | None = None,
        slot: int | None = None,
    ) -> None:
        if texture is not None:
            self.texture = texture

        if slot is not None:
            self.slot = int(slot)

        self.ask_update()

    def apply(
        self,
        *_: Any,
    ) -> None:
        self.texture.bind_to(
            self.slot,
        )

        GL.active_texture(
            0,
        )


class BindTexture(InstructionGroup):
    def __init__(
        self,
        *,
        uniform: str,
        texture: Texture2D | TextureCube,
        slot: int,
    ) -> None:
        super().__init__()

        self.uniform = uniform

        self.bind_callback = BindTextureCallback(
            texture=texture,
            slot=slot,
        )

        self.sampler = BindUniform(
            uniform,
            int(slot),
        )

        self.add(
            self.bind_callback,
        )

        self.add(
            self.sampler,
        )

    @property
    def texture(
        self,
    ) -> Texture2D | TextureCube:
        return self.bind_callback.texture

    @texture.setter
    def texture(
        self,
        texture: Texture2D | TextureCube,
    ) -> None:
        self.bind_callback.sync(
            texture=texture,
        )

    @property
    def slot(
        self,
    ) -> int:
        return self.bind_callback.slot

    @slot.setter
    def slot(
        self,
        slot: int,
    ) -> None:
        slot = int(slot)

        self.bind_callback.sync(
            slot=slot,
        )

        self.sampler.sync(
            slot,
        )

    def sync(
        self,
        *,
        texture: Texture2D | TextureCube | None = None,
        slot: int | None = None,
    ) -> None:
        if texture is not None:
            self.texture = texture

        if slot is not None:
            self.slot = slot




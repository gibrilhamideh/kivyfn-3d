# kivyfn/three/skinning/skinned_mesh.py

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.skinning.palette import SkinPalette

if TYPE_CHECKING:
    from kivyfn.three.skinning.skin import Skin
    from kivyfn.three.skinning.skinned_model import SkinnedModel3D


class SkinnedMesh3D(Object3D):
    """
    One renderable skinned mesh layer.

    This is not the whole animated body. It is one visible mesh that uses the
    shared Skin owned by a SkinnedModel3D and owns its own SkinPalette.

    Examples:
        body mesh
        shirt mesh
        pants mesh
        armor mesh
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            *args,
            **kwargs,
        )

        self.skin_palette = SkinPalette()
        self._skinned_model: SkinnedModel3D | None = None

    @property
    def kind(
        self,
    ):
        return "skinned_mesh"

    @property
    def skinned_model(
        self,
    ) -> SkinnedModel3D | None:
        return self._skinned_model

    def require_skinned_model(
        self,
    ) -> SkinnedModel3D:
        if self._skinned_model is None:
            raise ValueError(
                f"SkinnedMesh3D {self.name!r} is not attached to a "
                "SkinnedModel3D."
            )

        return self._skinned_model

    @property
    def skin(
        self,
    ) -> Skin | None:
        if self._skinned_model is None:
            return None

        return self._skinned_model.skin

    def require_skin(
        self,
    ) -> Skin:
        return self.require_skinned_model().skin

    def sync_skin_palette(
        self,
    ) -> None:
        self.skin_palette.sync_palette(
            mesh=self,
            skin=self.require_skin(),
        )

    def clear_skin_palette(
        self,
    ) -> None:
        self.skin_palette.clear()

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kivyfn.three.objects.object3d import Object3D

class RenderLinkFilter:

    def __call__(self, object3d: Object3D) -> bool:
        return True

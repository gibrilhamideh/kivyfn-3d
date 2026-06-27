# kivyfn/three/meshes/quad.py

from __future__ import annotations

from typing import Final

from kivy.graphics import Mesh

from kivyfn.three.views.rect import ViewRect


__all__ = [
    "Quad",
]


_QUAD_INDICES: Final[list[int]] = [
    0,
    1,
    2,
    2,
    3,
    0,
]

_QUAD_FORMAT: Final[list[tuple[bytes, int, str]]] = [
    (b"v_pos", 2, "float"),
    (b"v_tc0", 2, "float"),
]


class Quad:
    @staticmethod
    def create(
        *,
        rect: ViewRect,
        viewport: ViewRect,
        uv_rect: ViewRect | None = None,
    ) -> Mesh:
        return Mesh(
            vertices=Quad._vertices(
                rect=rect,
                viewport=viewport,
                uv_rect=uv_rect,
            ),
            indices=list(_QUAD_INDICES),
            fmt=list(_QUAD_FORMAT),
            mode="triangles",
        )

    @staticmethod
    def update(
        mesh: Mesh,
        *,
        rect: ViewRect,
        viewport: ViewRect,
        uv_rect: ViewRect | None = None,
    ) -> None:
        mesh.vertices = Quad._vertices(
            rect=rect,
            viewport=viewport,
            uv_rect=uv_rect,
        )

    @staticmethod
    def _vertices(
        *,
        rect: ViewRect,
        viewport: ViewRect,
        uv_rect: ViewRect | None,
    ) -> list[float]:
        left, bottom, right, top = Quad._ndc_rect(
            rect=rect,
            viewport=viewport,
        )

        u0, v0, u1, v1 = Quad._uv_rect(
            uv_rect,
        )

        return [
            left,
            bottom,
            u0,
            v0,

            right,
            bottom,
            u1,
            v0,

            right,
            top,
            u1,
            v1,

            left,
            top,
            u0,
            v1,
        ]

    @staticmethod
    def _ndc_rect(
        *,
        rect: ViewRect,
        viewport: ViewRect,
    ) -> tuple[float, float, float, float]:
        if viewport.width <= 0.0 or viewport.height <= 0.0:
            raise RuntimeError(
                "Cannot create quad because viewport size is invalid: "
                f"{viewport.width}x{viewport.height}."
            )

        left = Quad._ndc_x(
            rect.x,
            viewport,
        )
        right = Quad._ndc_x(
            rect.x + rect.width,
            viewport,
        )

        bottom = Quad._ndc_y(
            rect.y,
            viewport,
        )
        top = Quad._ndc_y(
            rect.y + rect.height,
            viewport,
        )

        return (
            left,
            bottom,
            right,
            top,
        )

    @staticmethod
    def _ndc_x(
        x: float,
        viewport: ViewRect,
    ) -> float:
        return (
            (
                (x - viewport.x)
                / viewport.width
            )
            * 2.0
            - 1.0
        )

    @staticmethod
    def _ndc_y(
        y: float,
        viewport: ViewRect,
    ) -> float:
        return (
            (
                (y - viewport.y)
                / viewport.height
            )
            * 2.0
            - 1.0
        )

    @staticmethod
    def _uv_rect(
        uv_rect: ViewRect | None,
    ) -> tuple[float, float, float, float]:
        if uv_rect is None:
            return (
                0.0,
                0.0,
                1.0,
                1.0,
            )

        return (
            uv_rect.x,
            uv_rect.y,
            uv_rect.x + uv_rect.width,
            uv_rect.y + uv_rect.height,
        )

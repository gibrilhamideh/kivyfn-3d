# kivyfn/three/graphics/gl/screen.py

from __future__ import annotations

from typing import Any


from kivyfn.three.graphics.gl.targets.base import BaseTargetContext, RenderFrame
from kivyfn.three.views.viewport import Viewport
from kivyfn.three.views.view import View


class ScreenTarget(BaseTargetContext):

    def __init__(
        self,
        view: View,
        viewport: Viewport,
        depth_test: bool,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            view=view,
            viewport=viewport,
            **kwargs
        )

        self.depth_test = depth_test

        self.build(
            RenderFrame(
                begin=self.begin,
                end=self.end,
            )
        )


    # =================================== #
    # Build Helpers
    # =================================== #

    def begin(self, *_: Any) -> None:
        self.viewport.apply()

        if self.depth_test:
            self.enable_depthtest()

    def end(self, *_: Any) -> None:

        if self.depth_test:
            self.disable_depthtest()

        self.viewport.restore()


    def delete(self):
        self.clear_all()


    # =================================== #
    # Views
    # =================================== #
    def sync_view(
        self,
        *_
    ) -> None:

        view = self.view
        aspect = self.viewport.aspect

        projection_mat = view.get_projection_matrix(mode="planar", aspect=aspect).to_uniform()
        self.apply_uniform("projection_mat", projection_mat)

        view_mat = view.get_view_matrix(mode="planar").to_uniform()
        self.apply_uniform("view_mat", view_mat)

        camera_position = view.get_camera_position()
        self.apply_uniform("camera_position", camera_position)

        self.ask_update()



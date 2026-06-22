# kivyfn/three/views/camera.py

from __future__ import annotations
from typing import Literal
from weakref import WeakSet

from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, ObjectProperty, OptionProperty

from kivyfn.three.math.vector import Vector3
from kivyfn.three.views.viewport import Viewport


class Camera(EventDispatcher):
    position: Vector3 = ObjectProperty(None, allownone=True)
    target: Vector3 = ObjectProperty(None, allownone=True)
    up: Vector3 = ObjectProperty(None, allownone=True)

    fov: float = NumericProperty(45.0)
    near: float = NumericProperty(1.0)
    far: float = NumericProperty(1000.0)

    ortho_size: float = NumericProperty(20.0)
    projection: Literal[
        "perspective",
        "orthographic"
        ] = OptionProperty("perspective", options=["perspective", "orthographic"])


    def __init__(
        self,
        position: Vector3 | None = None,
        target: Vector3 | None = None,
        up: Vector3 | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self._viewports: WeakSet[Viewport] = WeakSet()

        self.position = position or Vector3(0.0, 0.0, 10.0)
        self.target = target or Vector3.zero()
        self.up = up or Vector3(0.0, 1.0, 0.0)

        self.bind(
            position=self.sync,
            target=self.sync,
            up=self.sync,
            fov=self.sync,
            near=self.sync,
            far=self.sync,
            ortho_size=self.sync,
            projection=self.sync,
        )

    def attach(
        self,
        viewport: Viewport,
    ) -> Viewport:
        self._viewports.add(viewport)
        self.sync_viewport(viewport)
        return viewport

    def detach(
        self,
        viewport: Viewport,
    ) -> None:
        self._viewports.discard(viewport)

    def sync(
        self,
        *_,
    ) -> None:
        for viewport in list(self._viewports):
            self.sync_viewport(viewport)

    def sync_viewport(
        self,
        viewport: Viewport,
    ) -> None:
        view = viewport.view

        view.position = self.position
        view.target = self.target
        view.up = self.up

        view.fov = self.fov
        view.near = self.near
        view.far = self.far
        view.ortho_size = self.ortho_size
        view.projection = self.projection

    def set_look_at(
        self,
        position: Vector3,
        target: Vector3,
        up: Vector3 | None = None,
    ) -> None:
        self.position = position
        self.target = target

        if up is not None:
            self.up = up

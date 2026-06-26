# kivyfn/three/views/viewport.py

from __future__ import annotations

from typing import Any, Literal

from kivy.event import EventDispatcher
from kivy.graphics.opengl import GL_VIEWPORT, glGetIntegerv, glViewport
from kivy.properties import (
        AliasProperty,
        NumericProperty,
        ObjectProperty,
        ReferenceListProperty,
        OptionProperty
)

from kivyfn.three.views.rect import ViewRect


class Viewport(EventDispatcher):

    x: float = NumericProperty(0.0)
    y: float = NumericProperty(0.0)
    width: float = NumericProperty(1.0)
    height: float = NumericProperty(1.0)

    local_viewport: LocalViewport = ObjectProperty()
    scene_viewport: LocalViewport = ObjectProperty()

    pos = ReferenceListProperty(
        x,
        y,
    )

    size = ReferenceListProperty(
        width,
        height,
    )

    source: Literal["scene", "local"] = OptionProperty(
        "scene",
        options=[
            "scene",
            "local",
        ],
    )

    __events__ = (
        "on_dirty",
    )

    def __init__(
        self,
        local_viewport: LocalViewport,
        scene_viewport: LocalViewport,
        *,
        source: Literal["scene", "local"] = "scene",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.local_viewport = local_viewport
        self.scene_viewport = scene_viewport
        self.source: Literal["scene", "local"] = source

        self._previous_size: tuple[int, int, int, int] | None = None

        self.bind(
            x=self._mark_dirty,
            y=self._mark_dirty,
            width=self._mark_dirty,
            height=self._mark_dirty,
            source=self._rebind_viewport,
        )

        self._rebind_viewport()

    # =================================== #
    # Bind
    # =================================== #
    def _rebind_viewport(self):

        if self.source == "local":

            self.x = self.local_viewport.x
            self.y = self.local_viewport.y
            self.width = self.local_viewport.width
            self.height = self.local_viewport.height

            self.local_viewport.bind(
                x=self.setter("x"),
                y=self.setter("y"),
                width=self.setter("width"),
                height=self.setter("height"),
            )

            self.scene_viewport.unbind(
                x=self.setter("x"),
                y=self.setter("y"),
                width=self.setter("width"),
                height=self.setter("height"),
            )

            return

        self.x = self.scene_viewport.x
        self.y = self.scene_viewport.y
        self.width = self.scene_viewport.width
        self.height = self.scene_viewport.height

        self.local_viewport.unbind(
            x=self.setter("x"),
            y=self.setter("y"),
            width=self.setter("width"),
            height=self.setter("height"),
        )

        self.scene_viewport.bind(
            x=self.setter("x"),
            y=self.setter("y"),
            width=self.setter("width"),
            height=self.setter("height"),
        )

    # =================================== #
    # Rect
    # =================================== #
    @property
    def rect(self) -> ViewRect:
        return ViewRect(
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
        )

    # =================================== #
    # Aspect
    # =================================== #

    def _get_aspect(self) -> float:
        if self.width <= 0 or self.height <= 0:
            raise RuntimeError(
                "Cannot calculate viewport aspect because "
                f"viewport size is invalid: {self.width}x{self.height}."
            )

        return self.width / self.height

    aspect: float = AliasProperty(
        _get_aspect,
        None,
        bind=(
            "width",
            "height",
        ),
    )

    # =================================== #
    # GL
    # =================================== #

    def apply(self, *_) -> None:
        if self.width <= 0 or self.height <= 0:
            raise RuntimeError(
                "Cannot apply GL viewport because "
                f"viewport size is invalid: {self.width}x{self.height}."
            )

        previous = glGetIntegerv(GL_VIEWPORT)

        self._previous_size = (
            int(previous[0]),
            int(previous[1]),
            int(previous[2]),
            int(previous[3]),
        )

        glViewport(
            int(self.x),
            int(self.y),
            int(self.width),
            int(self.height),
        )

    def restore(self, *_) -> None:
        if self._previous_size is None:
            return

        x, y, width, height = self._previous_size

        glViewport(
            x,
            y,
            width,
            height,
        )

        self._previous_size = None

    # =================================== #
    # Events
    # =================================== #

    def _mark_dirty(
        self,
        *_: Any,
    ) -> None:
        self.dispatch("on_dirty")

    def on_dirty(self) -> None:
        pass


class LocalViewport(EventDispatcher):
    x: float = NumericProperty(0.0)
    y: float = NumericProperty(0.0)
    width: float = NumericProperty(1.0)
    height: float = NumericProperty(1.0)

    origin_x: float = NumericProperty(0.0)
    origin_y: float = NumericProperty(0.0)

    local_viewport = ObjectProperty()
    scene_viewport = ObjectProperty()

    pos = ReferenceListProperty(
        x,
        y,
    )

    size = ReferenceListProperty(
        width,
        height,
    )

    origin = ReferenceListProperty(
        origin_x,
        origin_y,
    )


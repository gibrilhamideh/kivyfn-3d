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


class ViewportBase(EventDispatcher):
    __events__ = (
        "on_dirty",
    )

    x: float = NumericProperty(0.0)
    y: float = NumericProperty(0.0)
    width: float = NumericProperty(1.0)
    height: float = NumericProperty(1.0)

    pos = ReferenceListProperty(
        x,
        y,
    )

    size = ReferenceListProperty(
        width,
        height,
    )

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.bind(
            x=self._mark_dirty,
            y=self._mark_dirty,
            width=self._mark_dirty,
            height=self._mark_dirty,
        )

    @property
    def rect(self) -> ViewRect:
        return ViewRect(
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
        )

    def _get_aspect(self) -> float:
        return self.rect.aspect

    aspect: float = AliasProperty(
        _get_aspect,
        None,
        bind=(
            "width",
            "height",
        ),
    )

    def _mark_dirty(
        self,
        *_: Any,
    ) -> None:
        self.dispatch("on_dirty")

    def on_dirty(
        self,
    ) -> None:
        pass

class Viewport(ViewportBase):

    local_viewport: LocalViewport = ObjectProperty()
    scene_viewport: SceneViewport = ObjectProperty()

    source: Literal["scene", "local"] = OptionProperty(
        "scene",
        options=[
            "scene",
            "local",
        ],
    )


    def __init__(
        self,
        local_viewport: LocalViewport,
        scene_viewport: SceneViewport,
        *,
        source: Literal["scene", "local"] = "scene",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.local_viewport = local_viewport
        self.scene_viewport = scene_viewport
        self.source = source

        self._previous_size: tuple[int, int, int, int] | None = None

        self.bind(
            source=self._sync,
        )

        self.local_viewport.bind(
            x=self._sync,
            y=self._sync,
            width=self._sync,
            height=self._sync,
        )

        self.scene_viewport.bind(
            x=self._sync,
            y=self._sync,
            width=self._sync,
            height=self._sync,
        )

        self._sync()

    # =================================== #
    # Sync
    # =================================== #

    def _sync(
        self,
        *_: Any,
    ) -> None:
        if self.source == "scene":
            self.x = self.scene_viewport.x
            self.y = self.scene_viewport.y
            self.width = self.scene_viewport.width
            self.height = self.scene_viewport.height
            return

        if self.source == "local":
            self.x = self.scene_viewport.x + self.local_viewport.x
            self.y = self.scene_viewport.y + self.local_viewport.y
            self.width = self.local_viewport.width
            self.height = self.local_viewport.height
            return

        raise RuntimeError(
            f"Unknown viewport source: {self.source!r}"
        )

    # =================================== #
    # GL
    # =================================== #

    def apply(
        self,
        *_: Any,
    ) -> None:
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

    def override(
        self,
        *,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> None:
        if width <= 0 or height <= 0:
            raise RuntimeError(
                "Cannot override GL viewport because "
                f"viewport size is invalid: {width}x{height}."
            )

        previous = glGetIntegerv(GL_VIEWPORT)

        self._previous_size = (
            int(previous[0]),
            int(previous[1]),
            int(previous[2]),
            int(previous[3]),
        )

        glViewport(
            int(x),
            int(y),
            int(width),
            int(height),
        )

    def restore(
        self,
        *_: Any,
    ) -> None:
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




class LocalViewport(ViewportBase):
    pass

class SceneViewport(ViewportBase):
    pass

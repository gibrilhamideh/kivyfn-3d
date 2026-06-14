from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.uix.widget import Widget

from kivyfn.three.overlays.attachment import Attachment
from kivyfn.three.math.vector import Vector2, Vector3

if TYPE_CHECKING:
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.scene.scene import Scene


class AttachmentManager:
    def __init__(
        self,
        scene: Scene,
        *,
        layer: Widget | None = None,
    ):
        self.scene = scene
        self.layer = layer or scene

        self._attachments: list[Attachment] = []
        self._attachments_by_widget: dict[Widget, Attachment] = {}
        self._attachments_by_anchor: dict[Node3D, list[Attachment]] = {}
        self._attachments_by_view: dict[str, list[Attachment]] = {}

        self._dirty = True

        self.scene.bind(
            pos=self._on_viewport_dirty,
            size=self._on_viewport_dirty,
        )

        self.scene.views.bind(
            on_view_dirty=self._on_view_dirty,
        )

    def attach(
        self,
        anchor: Node3D,
        widget: Widget,
        *,
        view_name: str = "main",
        offset: Vector2 | None = None,
        world_offset: Vector3 | None = None,
        hide_when_offscreen: bool = True,
    ) -> Attachment:
        if widget in self._attachments_by_widget:
            raise ValueError("Widget is already attached.")

        attachment = Attachment(
            scene=self.scene,
            anchor=anchor,
            widget=widget,
            view_name=view_name,
            offset=offset or Vector2.zero(),
            world_offset=world_offset or Vector3.zero(),
            hide_when_offscreen=hide_when_offscreen,
        )

        self._attachments.append(attachment)
        self._attachments_by_widget[widget] = attachment
        self._attachments_by_anchor.setdefault(anchor, []).append(attachment)
        self._attachments_by_view.setdefault(view_name, []).append(attachment)

        anchor.bind(
            on_transform_dirty=self._on_anchor_dirty,
            on_visibility_dirty=self._on_anchor_dirty,
        )

        self.layer.add_widget(widget)

        attachment.update()
        self.mark_dirty()

        return attachment

    def detach(self, attachment: Attachment) -> None:
        if attachment not in self._attachments:
            return

        self._attachments.remove(attachment)
        self._attachments_by_widget.pop(attachment.widget, None)

        anchor_items = self._attachments_by_anchor.get(attachment.anchor)

        if anchor_items is not None:
            if attachment in anchor_items:
                anchor_items.remove(attachment)

            if not anchor_items:
                self._attachments_by_anchor.pop(attachment.anchor, None)

                attachment.anchor.unbind(
                    on_transform_dirty=self._on_anchor_dirty,
                    on_visibility_dirty=self._on_anchor_dirty,
                )

        view_items = self._attachments_by_view.get(attachment.view_name)

        if view_items is not None:
            if attachment in view_items:
                view_items.remove(attachment)

            if not view_items:
                self._attachments_by_view.pop(attachment.view_name, None)

        attachment.destroy()
        self.mark_dirty()

    def detach_widget(self, widget: Widget) -> None:
        attachment = self._attachments_by_widget.get(widget)

        if attachment is not None:
            self.detach(attachment)

    def detach_anchor(self, anchor: Node3D) -> None:
        for attachment in list(self._attachments_by_anchor.get(anchor, [])):
            self.detach(attachment)

    def clear(self) -> None:
        for attachment in list(self._attachments):
            self.detach(attachment)

    def mark_dirty(self) -> None:
        self._dirty = True

    def update(self, *, force: bool = False) -> None:
        if not force and not self._dirty:
            return

        for attachment in self._attachments:
            attachment.update()

        self._dirty = False

    def update_view(self, view_name: str) -> None:
        for attachment in self._attachments_by_view.get(view_name, []):
            attachment.update()

    def destroy(self) -> None:
        self.clear()

        self.scene.unbind(
            pos=self._on_viewport_dirty,
            size=self._on_viewport_dirty,
        )

        self.scene.views.unbind(
            on_view_dirty=self._on_view_dirty,
        )

    def _on_anchor_dirty(self, *_):
        self.mark_dirty()

    def _on_view_dirty(self, _view_manager, view, _stage_name):
        self.update_view(view.name)

    def _on_viewport_dirty(self, *_):
        self.mark_dirty()

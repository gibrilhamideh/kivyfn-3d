# kivyfn/three/scene/view_manager.py

from __future__ import annotations

from collections.abc import Iterator

from kivy.event import EventDispatcher

from kivyfn.three.views.view import View


class ViewManager(EventDispatcher):
    __events__ = ("on_view_dirty", )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._views: dict[str, View] = {}
        self._view_stages: dict[str, set[str]] = {}

    def __contains__(self, name: str) -> bool:
        return name in self._views

    def __getitem__(self, name: str) -> View:
        return self.require(name)

    def __iter__(self) -> Iterator[View]:
        return iter(self._views.values())

    def __len__(self) -> int:
        return len(self._views)

    def __repr__(self) -> str:
        return (
            "ViewManager(\n"
            f"  views={list(self._views.keys())!r},\n"
            f"  view_contexts={self.stage_map}\n"
            ")"
        )

    # =================================== #
    # Properties
    # =================================== #

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._views.keys())

    @property
    def views(self) -> tuple[View, ...]:
        return tuple(self._views.values())

    @property
    def stage_map(self) -> dict[str, tuple[str, ...]]:
        return {
            view_name: tuple(sorted(context_names))
            for view_name, context_names in self._view_stages.items()
        }

    # =================================== #
    # View Management
    # =================================== #

    def create(
        self,
        name: str,
        *,
        replace: bool = False,
        **kwargs,
    ) -> View:
        view = View(
            name=name,
            **kwargs,
        )

        return self.add(
            view,
            replace=replace,
        )

    def add(
        self,
        view: View,
        *,
        replace: bool = False,
    ) -> View:
        if not view.name:
            raise ValueError("View must have a non-empty name.")

        if view.name in self._views and not replace:
            raise ValueError(f"View already exists: {view.name!r}")

        old_view = self._views.get(view.name)

        if old_view is not None:
            self._unbind_view(old_view)

        self._views[view.name] = view
        self._view_stages.setdefault(view.name, set())

        self._bind_view(view)
        self._dispatch_dirty(view)

        return view

    def get(
        self,
        name: str,
    ) -> View | None:

        return self._views.get(name)

    def require(
        self,
        name: str,
    ) -> View:

        view = self._views.get(name)
        if view is None:
            raise ValueError(f"View not found: {name!r}")

        return view

    def remove(self, name: str) -> View | None:
        view = self._views.pop(name, None)

        if view is None:
            return None

        self._unbind_view(view)
        self._view_stages.pop(name, None)

        return view

    def clear(self) -> None:
        for view in self._views.values():
            self._unbind_view(view)

        self._views.clear()
        self._view_stages.clear()

    # =================================== #
    # Context Links
    # =================================== #

    def link(
        self,
        view_name: str,
        context_name: str,
        *,
        sync: bool = True,
    ) -> None:
        view = self.require(view_name)

        contexts = self._view_stages.setdefault(
            view.name,
            set(),
        )

        contexts.add(context_name)

        if sync:
            self._dispatch_dirty(view)

    def unlink(
        self,
        view_name: str,
        context_name: str,
        *,
        sync: bool = True,
    ) -> None:
        view = self.require(view_name)

        contexts = self._view_stages.get(view.name)

        if contexts is None:
            return

        contexts.discard(context_name)

        if sync:
            self._dispatch_dirty(view)

    def unlink_context(
        self,
        context_name: str,
        *,
        sync: bool = True,
    ) -> None:
        changed_views: list[View] = []

        for view_name, contexts in self._view_stages.items():
            if context_name not in contexts:
                continue

            contexts.discard(context_name)

            if sync and view_name in self._views:
                changed_views.append(self._views[view_name])

        for view in changed_views:
            self._dispatch_dirty(view)

    def get_links(
        self,
    ) -> tuple[tuple[View, tuple[str, ...]], ...]:
        return tuple(
            (
                view,
                self.stages_for(view.name),
            )
            for view in self._views.values()
        )

    def stages_for(
        self,
        view_name: str,
    ) -> tuple[str, ...]:
        self.require(view_name)

        return tuple(
            sorted(
                self._view_stages.get(
                    view_name,
                    set(),
                )
            )
        )

    def view_for_stage(
        self,
        context_name: str,
    ) -> View | None:
        for view_name, contexts in self._view_stages.items():
            if context_name in contexts:
                return self._views.get(view_name)

        return None

    # =================================== #
    # Events
    # =================================== #

    def on_view_dirty(
        self,
        view: View,
        name: str,
    ) -> None:
        pass

    # =================================== #
    # Internal
    # =================================== #

    def _bind_view(self, view: View) -> None:
        view.bind(position=self._on_view_changed)
        view.bind(target=self._on_view_changed)
        view.bind(up=self._on_view_changed)
        view.bind(fov=self._on_view_changed)
        view.bind(near=self._on_view_changed)
        view.bind(far=self._on_view_changed)
        view.bind(ortho_size=self._on_view_changed)
        view.bind(perspective=self._on_view_changed)
        view.bind(projection_type=self._on_view_changed)

    def _unbind_view(self, view: View) -> None:
        view.unbind(position=self._on_view_changed)
        view.unbind(target=self._on_view_changed)
        view.unbind(up=self._on_view_changed)
        view.unbind(fov=self._on_view_changed)
        view.unbind(near=self._on_view_changed)
        view.unbind(far=self._on_view_changed)
        view.unbind(ortho_size=self._on_view_changed)
        view.unbind(perspective=self._on_view_changed)
        view.unbind(projection_type=self._on_view_changed)

    def _on_view_changed(self, view: View, value) -> None:
        self._dispatch_dirty(view)

    def _dispatch_dirty(self, view: View) -> None:
        context_names = self.stages_for(view.name)

        for name in context_names:
            self.dispatch(
                "on_view_dirty",
                view,
                name,
            )

# kivyfn/three/render/shader.py

from __future__ import annotations

from os import fsdecode
from pathlib import Path
from typing import Any, Literal

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty


ShaderReloadEvent = Literal[
    "manual",
    "modified",
    "created",
    "moved",
]


class Shader(EventDispatcher):
    name = StringProperty("")
    path = ObjectProperty(None, allownone=True)
    hot_reload = BooleanProperty(False)

    __events__ = (
        "on_reload",
    )

    def __init__(
        self,
        path: str | Path | None = None,
        name: str = "",
        **kwargs: Any,
    ):
        super().__init__(**kwargs)

        self._observer = None
        self._handler = None
        self._reload_event = None
        self._pending_reload_type: ShaderReloadEvent = "manual"
        self._pending_reload_path: Path | None = None

        self.name = name

        if path is not None:
            self.path = Path(path)


    def __repr__(self) -> str:
        return (
            "Shader(\n"
            f"  name={self.name!r},\n"
            f"  path={self.path!r},\n"
            f"  hot_reload={self.hot_reload}\n"
            ")"
        )

    def on_hot_reload(
        self,
        instance,
        value: bool,
    ) -> None:
        if value:
            self._start_hot_reload()
        else:
            self._stop_hot_reload()

    def on_path(
        self,
        instance,
        value: Path | None,
    ) -> None:
        if self.hot_reload:
            self._stop_hot_reload()
            self._start_hot_reload()

    def destroy(self) -> None:
        self._stop_hot_reload()

    def reload(
        self,
        event_type: ShaderReloadEvent = "manual",
        path: str | Path | None = None,
    ) -> None:
        if path is not None:
            new_path = Path(path)

            if self.path != new_path:
                self.path = new_path

        self.dispatch(
            "on_reload",
            event_type,
            self.path,
        )

    def on_reload(
        self,
        event_type: ShaderReloadEvent,
        path: Path | None,
    ) -> None:
        pass

    def _schedule_reload(
        self,
        event_type: ShaderReloadEvent,
        path: str | Path | None,
    ) -> None:
        self._pending_reload_type = event_type
        self._pending_reload_path = (
            Path(path)
            if path is not None
            else self.path
        )

        if self._reload_event is not None:
            self._reload_event.cancel()

        self._reload_event = Clock.schedule_once(
            self._dispatch_reload,
            0.15,
        )

    def _dispatch_reload(
        self,
        *_,
    ) -> None:
        self._reload_event = None

        self.reload(
            self._pending_reload_type,
            self._pending_reload_path,
        )

        self._pending_reload_type = "manual"
        self._pending_reload_path = None

    def _start_hot_reload(self) -> None:
        if self.path is None:
            return

        if self._observer is not None:
            return

        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError as exc:
            raise RuntimeError(
                "Shader hot_reload=True requires watchdog. "
                "Install it with: pip install watchdog"
            ) from exc

        shader = self
        watched_path = self.path.resolve()
        watched_dir = watched_path.parent

        class ShaderFileHandler(FileSystemEventHandler):
            def _path(
                self,
                value: str | bytes,
            ) -> Path:
                return Path(fsdecode(value))

            def _matches(
                self,
                value: str | bytes,
            ) -> bool:
                return self._path(value).resolve() == watched_path

            def _reload(
                self,
                event_type: ShaderReloadEvent,
                path: str | bytes,
            ) -> None:
                Clock.schedule_once(
                    lambda *_: shader._schedule_reload(
                        event_type,
                        self._path(path),
                    ),
                    0,
                )

            def on_modified(
                self,
                event,
            ) -> None:
                if not event.is_directory and self._matches(event.src_path):
                    self._reload(
                        "modified",
                        event.src_path,
                    )

            def on_created(
                self,
                event,
            ) -> None:
                if not event.is_directory and self._matches(event.src_path):
                    self._reload(
                        "created",
                        event.src_path,
                    )

            def on_moved(
                self,
                event,
            ) -> None:
                if not event.is_directory and self._matches(event.dest_path):
                    self._reload(
                        "moved",
                        event.dest_path,
                    )

        self._handler = ShaderFileHandler()
        self._observer = Observer()
        self._observer.schedule(
            self._handler,
            str(watched_dir),
            recursive=False,
        )
        self._observer.daemon = True
        self._observer.start()

    def _stop_hot_reload(self) -> None:
        if self._observer is None:
            return

        self._observer.stop()
        self._observer.join(timeout=1.0)

        self._observer = None
        self._handler = None

        if self._reload_event is not None:
            self._reload_event.cancel()
            self._reload_event = None

from __future__ import annotations

import numpy as np

import moderngl_window as mglw
from moderngl_window.context.pyglet.window import Window as PygletWindow
from moderngl_window.timers.clock import Timer
from screeninfo import get_monitors
from functools import wraps

from manimlib.config import get_global_config
from manimlib.constants import FRAME_SHAPE

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable, TypeVar, Optional
    from manimlib.scene.scene import Scene

    T = TypeVar("T")


class Window(PygletWindow):
    fullscreen: bool = False
    resizable: bool = True
    gl_version: tuple[int, int] = (3, 3)
    vsync: bool = True
    cursor: bool = True

    def __init__(
        self,
        scene: Optional[Scene] = None,
        size: tuple[int, int] = (1280, 720),
        default_position: tuple[int, int] = (0, 0),
        samples: int = 0
    ):
        super().__init__(size=size, samples=samples)

        self.scene = scene
        self.default_size = size
        self.default_position = default_position
        self.pressed_keys = set()
        self.size = size

        self.to_default_position()

        if self.scene:
            self.init_for_scene(scene)

    def init_for_scene(self, scene: Scene):
        """
        Resets the state and updates the scene associated to this window.

        This is necessary when we want to reuse an *existing* window after a
        `scene.reload()` was requested, which will create new scene instances.
        """
        self.pressed_keys.clear()
        self._has_undrawn_event = True

        self.scene = scene
        self.title = str(scene)

        self.init_mgl_context()

        self.timer = Timer()
        self.config = mglw.WindowConfig(ctx=self.ctx, wnd=self, timer=self.timer)
        mglw.activate_context(window=self, ctx=self.ctx)
        self.timer.start()

    def focus(self):
        """
        Puts focus on this window by hiding and showing it again.

        Note that the pyglet `activate()` method didn't work as expected here,
        so that's why we have to use this workaround. This will produce a small
        flicker on the window but at least reliably focuses it. It may also
        offset the window position slightly.
        """
        self._window.set_visible(False)
        self._window.set_visible(True)

    def to_default_position(self):
        self.position = self.default_position
        # Hack. Sometimes, namely when configured to open in a separate window,
        # the window needs to be resized to display correctly.
        w, h = self.default_size
        self.size = (w - 1, h - 1)
        self.size = (w, h)

    # Delegate event handling to scene
    def pixel_coords_to_space_coords(
        self,
        px: int,
        py: int,
        relative: bool = False
    ) -> np.ndarray:
        if self.scene is None or not hasattr(self.scene, "frame"):
            return np.zeros(3)

        pixel_shape = np.array(self.size)
        fixed_frame_shape = np.array(FRAME_SHAPE)
        frame = self.scene.frame

        coords = np.zeros(3)
        coords[:2] = (fixed_frame_shape / pixel_shape) * np.array([px, py])
        if not relative:
            coords[:2] -= 0.5 * fixed_frame_shape
        return frame.from_fixed_frame_point(coords, relative)

    def has_undrawn_event(self) -> bool:
        return self._has_undrawn_event

    def swap_buffers(self):
        super().swap_buffers()
        self._has_undrawn_event = False

    @staticmethod
    def note_undrawn_event(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self._has_undrawn_event = True
        return wrapper

    @note_undrawn_event
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        super().on_mouse_motion(x, y, dx, dy)
        if not self.scene:
            return
        point = self.pixel_coords_to_space_coords(x, y)
        d_point = self.pixel_coords_to_space_coords(dx, dy, relative=True)
        self.scene.on_mouse_motion(point, d_point)

    @note_undrawn_event
    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> None:
        super().on_mouse_drag(x, y, dx, dy, buttons, modifiers)
        if not self.scene:
            return
        point = self.pixel_coords_to_space_coords(x, y)
        d_point = self.pixel_coords_to_space_coords(dx, dy, relative=True)
        self.scene.on_mouse_drag(point, d_point, buttons, modifiers)

    @note_undrawn_event
    def on_mouse_press(self, x: int, y: int, button: int, mods: int) -> None:
        super().on_mouse_press(x, y, button, mods)
        if not self.scene:
            return
        point = self.pixel_coords_to_space_coords(x, y)
        self.scene.on_mouse_press(point, button, mods)

    @note_undrawn_event
    def on_mouse_release(self, x: int, y: int, button: int, mods: int) -> None:
        super().on_mouse_release(x, y, button, mods)
        if not self.scene:
            return
        point = self.pixel_coords_to_space_coords(x, y)
        self.scene.on_mouse_release(point, button, mods)

    @note_undrawn_event
    def on_mouse_scroll(self, x: int, y: int, x_offset: float, y_offset: float) -> None:
        super().on_mouse_scroll(x, y, x_offset, y_offset)
        if not self.scene:
            return
        point = self.pixel_coords_to_space_coords(x, y)
        offset = self.pixel_coords_to_space_coords(x_offset, y_offset, relative=True)
        self.scene.on_mouse_scroll(point, offset, x_offset, y_offset)

    @note_undrawn_event
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        self.pressed_keys.add(symbol)  # Modifiers?
        super().on_key_press(symbol, modifiers)
        if not self.scene:
            return
        self.scene.on_key_press(symbol, modifiers)

    @note_undrawn_event
    def on_key_release(self, symbol: int, modifiers: int) -> None:
        self.pressed_keys.difference_update({symbol})  # Modifiers?
        super().on_key_release(symbol, modifiers)
        if not self.scene:
            return
        self.scene.on_key_release(symbol, modifiers)

    @note_undrawn_event
    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        if not self.scene:
            return
        self.scene.on_resize(width, height)

    @note_undrawn_event
    def on_show(self) -> None:
        super().on_show()
        if not self.scene:
            return
        self.scene.on_show()

    @note_undrawn_event
    def on_hide(self) -> None:
        super().on_hide()
        if not self.scene:
            return
        self.scene.on_hide()

    @note_undrawn_event
    def on_close(self) -> None:
        super().on_close()
        if not self.scene:
            return
        self.scene.on_close()

    def is_key_pressed(self, symbol: int) -> bool:
        return (symbol in self.pressed_keys)

"""Capture inputs: a take the person records in the browser, read on demand.

A take is a file the browser made instead of one the person picked. So a
capture input is an upload input: the take stays a handle in the tab, the
value is its metadata, and every byte read is an interaction on the ref, the
same ``get_slice``, ``get_bytes``, ``open`` and ``pull`` an ``UploadFileRef``
has. Nothing new on the server: the intake and temp area of
``nustd.ui.uploads`` carry takes as they carry picks.

- ``MicCaptureRef``: a sound, from a microphone.
- ``CameraCaptureRef``: a photo or a video, from a camera.

One take per input; a new take replaces the old one. The device opens on the
person's first click, never on its own, and closes as soon as it is not in
use. ``on_status`` hears where the device and the recorder are.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

from nustd.ui.core import Changed, Write

from .input import _common, _Nullable
from .upload import _FileInput, _FileReads


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import IntArg, StrArg

    from ..vocab import ControlSize


__all__ = [
    "STATUS",
    "CameraCaptureRef",
    "CameraFacing",
    "CameraMode",
    "CameraResolution",
    "CaptureStatus",
    "MicCaptureRef",
    "PhotoFormat",
]


#: The event a capture input sends when its device or recorder moves.
STATUS = "status"

CaptureStatus = Literal["idle", "asking", "live", "recording", "paused", "blocked"]
CameraMode = Literal["photo", "video"]
CameraFacing = Literal["user", "environment"]
CameraResolution = Literal["sd", "hd", "fhd"]
PhotoFormat = Literal["jpeg", "webp", "png"]

_MODES = ("photo", "video")
_FACINGS = ("user", "environment")
_RESOLUTIONS = ("sd", "hd", "fhd")
_FORMATS = ("jpeg", "webp", "png")


def _one_of(name: str, value: object, allowed: tuple[str, ...]) -> str:
    """A choice from a fixed set, or a ValueError naming the set."""
    if value not in allowed:
        msg = f"{name} is one of {', '.join(allowed)}, not {value!r}"
        raise ValueError(msg)
    return value  # type: ignore[return-value]


def _seconds(name: str, value: object) -> int | None:
    """A duration in whole seconds: a positive int, or None for no limit."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        msg = f"{name} is a positive int of seconds or None, not {value!r}"
        raise ValueError(msg)
    return value


class _CaptureInput(_Nullable, _FileReads, _FileInput):
    """What both capture inputs are: a recorder whose take is a file. Abstract.

    The value is NULL while empty, then the upload file dict plus
    ``duration`` (seconds, pauses out, 0 for a photo) and ``width`` and
    ``height`` (pixels, 0 for sound). ``on_change`` hears a take kept or
    discarded by the person.
    """

    def on_status(self) -> Changed:
        """The device or the recorder moved: ``{event: "status", status, error}``.

        ``status`` is ``idle``, ``asking``, ``live``, ``recording``,
        ``paused`` or ``blocked``. ``error`` says why when blocked
        (``denied``, ``no_device``, ``busy``, ``insecure``, ``unsupported``,
        ``failed``), or ``lost`` when the device went away mid use; "" else.
        Sent on every move, whoever caused it.
        """
        return Changed(self, STATUS)

    def set_max_duration(self, seconds: IntArg | None) -> Nu:
        """The longest take, in seconds; recording stops itself there. None for no limit."""
        from nu.forms import Dict

        return Write(self, Dict.of(max_duration=seconds))


class MicCaptureRef(_CaptureInput):
    """A sound the person records with a microphone.

    One button records; pause, resume and stop follow, with the time and a
    live level meter. The take plays back in the kit audio row, to keep, re
    record or delete. The value is the take's file dict, NULL while empty;
    read its bytes with ``get_slice``, ``get_bytes`` or ``open`` as an
    ``UploadFileRef``'s.

    Args:
        max_duration: the longest take, in seconds; recording stops itself
            there and keeps the take. None for no limit.
        processing: echo cancellation, noise suppression and auto gain, the
            browser's voice cleanup. False for music or room sound.
        label: the label above the control.

    Notes:
        - The microphone opens on the first click, never on its own, and
          closes when the take is kept. A second take replaces the first
          only once it is kept; a canceled one leaves the first in place.
        - ``mime`` is what the browser records: ``audio/webm`` in Chrome and
          Firefox, ``audio/mp4`` in Safari.
        - ``on_status`` hears the device and the recorder; ``on_change`` a
          take kept or deleted.

    Example:
        memo = MicCaptureRef.slot(label="Voice memo", max_duration=120)
        nu.ReactEvery(memo.on_change(), nu.let(memo.get_bytes(), transcribe))
    """

    _wire_type = "MicCaptureRef"

    @classmethod
    def slot(
        cls,
        *,
        max_duration: int | None = None,
        processing: bool = True,
        label: str = "",
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            max_duration=_seconds("MicCaptureRef max_duration", max_duration),
            processing=bool(processing),
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )


class CameraCaptureRef(_CaptureInput):
    """A photo or a video the person takes with a camera.

    The camera opens into a live preview on the first click; a shutter takes
    a photo, or record, pause and stop make a video. The take shows in the
    kit image viewer or video player, to keep, retake or delete. The value
    is the take's file dict with ``width`` and ``height`` (and ``duration``
    for a video), NULL while empty.

    Args:
        mode: ``photo`` or ``video``.
        facing: the camera that opens first, ``user`` (front) or
            ``environment`` (back). The person can switch when there are two.
        resolution: the size asked of the camera, ``sd`` (640x480), ``hd``
            (1280x720) or ``fhd`` (1920x1080). A camera gives what it can.
        format: a photo's encoding, ``jpeg``, ``webp`` or ``png``.
        audio: a video records sound too.
        max_duration: the longest video, in seconds; None for no limit.
        aspect: the frame's css ratio (``"4/3"``); "" follows the camera.
        label: the label above the control.

    Notes:
        - The front camera's preview is mirrored, as a mirror reads; the
          photo and the video are not.
        - The camera closes once a take is kept, on delete, and when the tab
          is hidden while not recording, so its light is never left on.
        - ``mime`` of a video is what the browser records: ``video/webm`` in
          Chrome and Firefox, ``video/mp4`` in Safari.

    Example:
        shot = CameraCaptureRef.slot(label="Profile photo", format="webp", aspect="1/1")
        nu.ReactEvery(shot.on_change(), shot.pull())
    """

    _wire_type = "CameraCaptureRef"

    @classmethod
    def slot(
        cls,
        *,
        mode: CameraMode = "photo",
        facing: CameraFacing = "user",
        resolution: CameraResolution = "hd",
        format: PhotoFormat = "jpeg",
        audio: bool = True,
        max_duration: int | None = None,
        aspect: str = "",
        label: str = "",
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            mode=_one_of("CameraCaptureRef mode", mode, _MODES),
            facing=_one_of("CameraCaptureRef facing", facing, _FACINGS),
            resolution=_one_of("CameraCaptureRef resolution", resolution, _RESOLUTIONS),
            format=_one_of("CameraCaptureRef format", format, _FORMATS),
            audio=bool(audio),
            max_duration=_seconds("CameraCaptureRef max_duration", max_duration),
            aspect=aspect,
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set_mode(self, mode: CameraMode | StrArg) -> Nu:
        """Photo or video. A take already kept stays."""
        from nu.forms import Dict

        return Write(self, Dict.of(mode=mode))

    def set_facing(self, facing: CameraFacing | StrArg) -> Nu:
        """The camera the next open asks for: ``user`` or ``environment``."""
        from nu.forms import Dict

        return Write(self, Dict.of(facing=facing))

"""Time-based media leaves -- ``VideoRef`` and ``AudioRef``.

Server-owned and display only, like ``ImageRef``: the server writes the
source and how to show it, the browser plays it with the kit transport (play,
scrub, time, volume, speed, keys). Playback stays in the browser; nothing is
sent back. A write is a partial merge of props, so each setter sends only what
it names::

    class Clip(nustd.ui.Column):
        video = nustd.ui.VideoRef.slot(aspect="16/9", radius="md")
        take = nustd.ui.AudioRef.slot(title="take-01.mp3")

    Clip.video.set(files.url(bid), poster=files.url(still))
    Clip.take.set_src(files.url(audio_bid))

``AudioRef`` draws the sound's waveform when its source allows a CORS fetch,
a plain scrub bar when it does not. Autoplay only starts muted in most
browsers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core import Write

from .base import LeafRef


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import BoolArg, IntArg, StrArg


__all__ = ["AudioRef", "VideoRef"]


VideoFit = Literal["contain", "cover", "fill"]
VideoRadius = Literal["none", "sm", "md", "lg"]


class VideoRef(LeafRef):
    """Display-only video ref. One `write` op carries every mutation.

    `aspect` holds the frame to a ratio, spelled "16/9", "1:1" or a bare
    number like "1.5"; without one the frame takes the video's own shape once
    it loads. `radius` is the corner scale (none unless set), `fit` how the
    picture fills the frame.
    """

    _wire_type = "VideoRef"

    @classmethod
    def slot(
        cls,
        *,
        src: str = "",
        poster: str = "",
        fit: VideoFit = "contain",
        width: int | None = None,
        height: int | None = None,
        radius: VideoRadius | None = None,
        aspect: str = "",
        autoplay: bool = False,
        loop: bool = False,
        muted: bool = False,
    ) -> Self:
        return super().slot(
            src=src,
            poster=poster,
            fit=fit,
            width=width,
            height=height,
            radius=radius,
            aspect=aspect,
            autoplay=autoplay,
            loop=loop,
            muted=muted,
        )

    def set_src(self, url: StrArg) -> Nu:
        return Write(self, Dict.of(src=url))

    def set_poster(self, url: StrArg) -> Nu:
        return Write(self, Dict.of(poster=url))

    def set_fit(self, mode: VideoFit | StrArg) -> Nu:
        return Write(self, Dict.of(fit=mode))

    def set_size(self, width: IntArg | None, height: IntArg | None) -> Nu:
        return Write(self, Dict.of(width=width, height=height))

    def set_radius(self, name: VideoRadius | StrArg | None) -> Nu:
        return Write(self, Dict.of(radius=name))

    def set_aspect(self, ratio: StrArg) -> Nu:
        return Write(self, Dict.of(aspect=ratio))

    def set_autoplay(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(autoplay=flag))

    def set_loop(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(loop=flag))

    def set_muted(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(muted=flag))

    def set(
        self,
        src: StrArg,
        poster: StrArg = UNSET,
        fit: VideoFit | StrArg = UNSET,
        autoplay: BoolArg = UNSET,
        loop: BoolArg = UNSET,
        muted: BoolArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"src": src}
        if poster is not UNSET:
            payload["poster"] = poster
        if fit is not UNSET:
            payload["fit"] = fit
        if autoplay is not UNSET:
            payload["autoplay"] = autoplay
        if loop is not UNSET:
            payload["loop"] = loop
        if muted is not UNSET:
            payload["muted"] = muted
        return Write(self, Dict.of(**payload))


class AudioRef(LeafRef):
    """Display-only audio ref: one dense player row. One `write` op carries every mutation.

    `title` is shown before the waveform and names the player for screen
    readers.
    """

    _wire_type = "AudioRef"

    @classmethod
    def slot(
        cls,
        *,
        src: str = "",
        title: str = "",
        autoplay: bool = False,
        loop: bool = False,
    ) -> Self:
        return super().slot(src=src, title=title, autoplay=autoplay, loop=loop)

    def set_src(self, url: StrArg) -> Nu:
        return Write(self, Dict.of(src=url))

    def set_title(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(title=text))

    def set_autoplay(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(autoplay=flag))

    def set_loop(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(loop=flag))

    def set(
        self,
        src: StrArg,
        title: StrArg = UNSET,
        autoplay: BoolArg = UNSET,
        loop: BoolArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"src": src}
        if title is not UNSET:
            payload["title"] = title
        if autoplay is not UNSET:
            payload["autoplay"] = autoplay
        if loop is not UNSET:
            payload["loop"] = loop
        return Write(self, Dict.of(**payload))

"""VideoRef and AudioRef: what each slot seeds and what each setter puts on the wire."""

from __future__ import annotations

import asyncio

import nu
from nu import Context, Shape
from nustd.ui import AudioRef, Column, Session, VideoRef
from nustd.ui.refs import Row


class _RecordingSession:
    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _mount(cls, **slot):
    sec = type("MSec", (Row,), {"m": cls.slot(**slot)})
    page = type("MPage", (Column,), {"sec": sec.slot()})
    app = type("MApp", (Shape,), {"page": page.slot()})
    return app.page.sec.m


def _frames(term):
    sess = _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


# --- VideoRef -------------------------------------------------------------------


def test_video_slot_seeds_every_prop():
    [frame] = _frames(_mount(VideoRef).set_src("/a.mp4"))
    wire_type, props = frame.chain[-1][1:]
    assert wire_type == "VideoRef"
    assert props == {
        "src": "",
        "poster": "",
        "fit": "contain",
        "width": None,
        "height": None,
        "radius": None,
        "aspect": "",
        "autoplay": False,
        "loop": False,
        "muted": False,
        "download": "",
    }
    assert frame.payload == {"src": "/a.mp4"}


def test_video_slot_takes_its_looks():
    [frame] = _frames(
        _mount(
            VideoRef,
            poster="/p.jpg",
            fit="cover",
            radius="md",
            aspect="16/9",
            loop=True,
            muted=True,
        ).set_src("/a.mp4")
    )
    props = frame.chain[-1][2]
    assert props["poster"] == "/p.jpg"
    assert props["fit"] == "cover"
    assert props["radius"] == "md"
    assert props["aspect"] == "16/9"
    assert props["loop"] is True
    assert props["muted"] is True


def test_video_set_sends_only_what_it_names():
    video = _mount(VideoRef)
    [frame] = _frames(video.set("/a.mp4", poster="/p.jpg", muted=True, autoplay=True))
    assert frame.payload == {"src": "/a.mp4", "poster": "/p.jpg", "autoplay": True, "muted": True}


def test_video_setters():
    video = _mount(VideoRef)
    cases = [
        (video.set_poster("/p.jpg"), {"poster": "/p.jpg"}),
        (video.set_fit("fill"), {"fit": "fill"}),
        (video.set_size(640, None), {"width": 640, "height": None}),
        (video.set_radius("lg"), {"radius": "lg"}),
        (video.set_aspect("4:3"), {"aspect": "4:3"}),
        (video.set_autoplay(True), {"autoplay": True}),
        (video.set_loop(True), {"loop": True}),
        (video.set_muted(False), {"muted": False}),
        (video.set_download("/a.mp4?download=1"), {"download": "/a.mp4?download=1"}),
    ]
    for term, payload in cases:
        [frame] = _frames(term)
        assert frame.payload == payload


# --- AudioRef -------------------------------------------------------------------


def test_audio_slot_seeds_every_prop():
    [frame] = _frames(_mount(AudioRef, title="take-01.mp3").set_src("/a.mp3"))
    wire_type, props = frame.chain[-1][1:]
    assert wire_type == "AudioRef"
    assert props == {
        "src": "",
        "title": "take-01.mp3",
        "autoplay": False,
        "loop": False,
        "download": "",
    }
    assert frame.payload == {"src": "/a.mp3"}


def test_audio_set_and_setters():
    audio = _mount(AudioRef)
    cases = [
        (audio.set("/a.mp3"), {"src": "/a.mp3"}),
        (
            audio.set("/a.mp3", title="roar", loop=True),
            {"src": "/a.mp3", "title": "roar", "loop": True},
        ),
        (audio.set_title("roar"), {"title": "roar"}),
        (audio.set_autoplay(True), {"autoplay": True}),
        (audio.set_loop(True), {"loop": True}),
        (audio.set_download("/a.mp3?download=1"), {"download": "/a.mp3?download=1"}),
    ]
    for term, payload in cases:
        [frame] = _frames(term)
        assert frame.payload == payload

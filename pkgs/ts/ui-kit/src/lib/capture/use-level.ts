// The loudness of a stream's sound, in [0, 1], for a meter.
//
// Web Audio taps the stream (an AnalyserNode, never connected to the
// speakers, so nothing echoes) and reads the RMS of the wave each frame. The
// value rises at once and falls slowly (a peak meter's decay), so speech
// reads as steady and not as flicker. Updates are held to about 30 a second.
//
// Off (no stream, no sound track, `on` false, no Web Audio) the level is 0
// and nothing runs. The AudioContext is closed with the stream.

import * as React from "react";

const FRAME_MS = 33;
/** How much of the last level stays each frame while the sound falls. */
const DECAY = 0.85;
/** RMS of loud speech sits near 0.3; this lifts it to fill the meter. */
const GAIN = 3;

export function useLevel(stream: MediaStream | null, on = true): number {
	const [level, setLevel] = React.useState(0);

	React.useEffect(() => {
		setLevel(0);
		if (!on || !stream || stream.getAudioTracks().length === 0) return;
		const Ctx =
			typeof window !== "undefined"
				? (window.AudioContext ??
					(window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext)
				: undefined;
		if (!Ctx) return;
		let ctx: AudioContext;
		try {
			ctx = new Ctx();
		} catch {
			return;
		}
		const source = ctx.createMediaStreamSource(stream);
		const analyser = ctx.createAnalyser();
		analyser.fftSize = 1024;
		source.connect(analyser);
		const wave = new Float32Array(analyser.fftSize);
		let held = 0;
		let last = 0;
		let frame = 0;
		const tick = (t: number) => {
			frame = requestAnimationFrame(tick);
			if (t - last < FRAME_MS) return;
			last = t;
			analyser.getFloatTimeDomainData(wave);
			let sum = 0;
			for (const v of wave) sum += v * v;
			const now = Math.min(1, Math.sqrt(sum / wave.length) * GAIN);
			held = now > held ? now : held * DECAY;
			setLevel(held < 0.005 ? 0 : held);
		};
		frame = requestAnimationFrame(tick);
		return () => {
			cancelAnimationFrame(frame);
			source.disconnect();
			void ctx.close().catch(() => {});
			setLevel(0);
		};
	}, [stream, on]);

	return level;
}

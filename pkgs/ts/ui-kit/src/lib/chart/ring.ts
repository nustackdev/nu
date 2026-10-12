// Fixed-size ring buffer: the window a streaming series keeps.
//
// A push past capacity overwrites the oldest item in place, so a chart fed a
// point per tick never copies or shifts its history. The array ECharts needs
// is built once per redraw by `toArray`, not once per point.

export class Ring<T> {
	private buf: (T | undefined)[];
	private cap: number;
	private start = 0;
	private len = 0;

	constructor(cap: number) {
		this.cap = Math.max(1, Math.floor(cap));
		this.buf = new Array(this.cap);
	}

	/** A ring seeded with the newest `cap` items of `items`. */
	static from<T>(items: readonly T[], cap: number): Ring<T> {
		const ring = new Ring<T>(cap);
		const from = Math.max(0, items.length - ring.cap);
		for (let i = from; i < items.length; i++) ring.push(items[i]);
		return ring;
	}

	get size(): number {
		return this.len;
	}

	get capacity(): number {
		return this.cap;
	}

	push(item: T): void {
		if (this.len < this.cap) {
			this.buf[(this.start + this.len) % this.cap] = item;
			this.len++;
			return;
		}
		this.buf[this.start] = item;
		this.start = (this.start + 1) % this.cap;
	}

	/** Oldest first. */
	toArray(): T[] {
		const out = new Array<T>(this.len);
		for (let i = 0; i < this.len; i++) out[i] = this.buf[(this.start + i) % this.cap] as T;
		return out;
	}

	/** Change the window, keeping the newest items that still fit. */
	resize(cap: number): void {
		const items = this.toArray();
		this.cap = Math.max(1, Math.floor(cap));
		this.buf = new Array(this.cap);
		this.start = 0;
		this.len = 0;
		const from = Math.max(0, items.length - this.cap);
		for (let i = from; i < items.length; i++) this.push(items[i]);
	}

	clear(): void {
		this.buf = new Array(this.cap);
		this.start = 0;
		this.len = 0;
	}
}

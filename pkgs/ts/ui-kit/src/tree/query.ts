// Query strings: one encoding, the same on both sides of the wire.
//
// The encoding is the browser's own `URLSearchParams`, the
// application/x-www-form-urlencoded set: a space is "+", letters, digits and
// `*-._` stay as they are, and every other byte of the UTF-8 is "%XX". The
// Python side (nustd.ui `encode_query` / `decode_query`) writes the same
// bytes, and one set of fixtures (tests/fixtures/query.json at the nu repo
// root) holds both to it.
//
// A query is a flat dict of strings. Decoding keeps the last value of a key
// that repeats. Encoding takes a few plain values and spells them one way:
//   - a string as is
//   - true / false as "true" / "false"
//   - a finite number as JS prints it (2 -> "2", 1.5 -> "1.5")
//   - null / undefined drops the key
// Anything else is `String(value)`, which is rarely what anyone wants: pass
// a string.

/** A URL's query as a flat dict. A key that repeats keeps its last value. */
export type Query = Record<string, string>;

/** A value a query can be built from. Null and undefined drop the key. */
export type QueryValue = string | number | boolean | null | undefined;

/** One value as the query spells it, or null for a key that drops. */
export function queryValue(value: QueryValue | unknown): string | null {
	if (value === null || value === undefined) return null;
	if (typeof value === "string") return value;
	if (typeof value === "boolean") return value ? "true" : "false";
	return String(value);
}

/** `search` (with or without the leading "?") as a dict. */
export function parseQuery(search: string): Query {
	const out: Query = {};
	for (const [key, value] of new URLSearchParams(search)) out[key] = value;
	return out;
}

/** `query` as a query string with no leading "?", in key order. */
export function serializeQuery(query: Record<string, QueryValue | unknown>): string {
	const params = new URLSearchParams();
	for (const [key, raw] of Object.entries(query)) {
		const value = queryValue(raw);
		if (value !== null) params.append(key, value);
	}
	return params.toString();
}

/**
 * `query` with `patch` merged over it: a key in the patch sets its value,
 * a null or undefined one drops the key. Keys keep their place; new ones
 * go at the end.
 */
export function mergeQuery(query: Query, patch: Record<string, QueryValue | unknown>): Query {
	const out: Query = { ...query };
	for (const [key, raw] of Object.entries(patch)) {
		const value = queryValue(raw);
		if (value === null) delete out[key];
		else out[key] = value;
	}
	return out;
}

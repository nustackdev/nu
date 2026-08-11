"""Solana JSON-RPC over a public mainnet endpoint via nu.http."""

import asyncio

import nu


_ENVELOPE = {"jsonrpc": "2.0", "id": 1}


class Solana(nu.Service):
    """Solana JSON-RPC: every method is POST / with the RPC method in the body."""

    get_slot = nu.http.POSTRef.method("/", method="getSlot", params=[], **_ENVELOPE)
    get_block = nu.http.POSTRef.method("/", method="getBlock", **_ENVELOPE)


app = nu.With(
    nu.http.bind(Solana, base_url="https://api.mainnet-beta.solana.com"),
    body=nu.Sequential(
        nu.print(nu.Dict(Solana.get_slot())["result"]),
        # nu.print(
        #     Solana.get_block(
        #         params=nu.List.of(300_000_000, {"maxSupportedTransactionVersion": 0}),
        #     ),
        # ),
    ),
)


if __name__ == "__main__":
    asyncio.run(nu.arun(app))

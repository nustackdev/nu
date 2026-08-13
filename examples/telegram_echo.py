"""Telegram echo bot from stock Nu blocks.

Uses only nu.http (Bot API sends + getUpdates long-poll) and nu.kv (offset
cursor). No new fabric, no new Ref types. The whole bot is one nu.With tree.

Set TG_TOKEN in the environment (from @BotFather), then:
    python examples/telegram_echo.py
"""

import asyncio
import os

import nu


TOKEN = os.environ["TG_TOKEN"]


# ---- Bot API: every method is POST /<name> on api.telegram.org ------------


class Bot(nu.Service):
    get_updates = nu.http.POSTRef.method("/getUpdates")
    send_message = nu.http.POSTRef.method("/sendMessage")


# ---- Poll cursor: last acked update_id, kv-backed -------------------------


class Cursor(nu.Shape):
    offset = nu.kv.IntRef.slot()


# ---- One poll tick: fetch batch, echo each message, bump offset -----------

msg = nu.Dict(nu.DictAttrRef("u")["message"])
handle_one = Bot.send_message(
    chat_id=nu.Dict(msg["chat"])["id"],
    text="echo: " + nu.Str(msg["text"]),
) >> Cursor.offset.set(nu.Int(nu.DictAttrRef("u")["update_id"]) + 1)

tick = nu.ForEachDo(
    nu.Dict(Bot.get_updates(offset=Cursor.offset, timeout=30))["result"], handle_one, item="u"
)


# ---- Assemble --------------------------------------------------------------

app = nu.With(
    nu.kv.memory_navigator(),
    nu.http.bind(Bot, base_url=f"https://api.telegram.org/bot{TOKEN}"),
    body=(
        nu.kv.auto_flow_atomic(Cursor.offset.init(0) >> nu.ForeverDo(nu.kv.auto_flow_atomic(tick)))
    ),
)


if __name__ == "__main__":
    asyncio.run(nu.arun(app))

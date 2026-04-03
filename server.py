import asyncio
import json
import os
import random

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 5000))

# Holds the first connected client (and their name) while waiting for a second.
_waiting: tuple[asyncio.StreamReader, asyncio.StreamWriter, str] | None = None
_lock = asyncio.Lock()


async def _send(writer: asyncio.StreamWriter, msg: dict) -> None:
    writer.write((json.dumps(msg) + "\n").encode())
    await writer.drain()


async def _recv(reader: asyncio.StreamReader) -> dict | None:
    try:
        line = await reader.readline()
        if not line:
            return None
        return json.loads(line.decode().strip())
    except (json.JSONDecodeError, asyncio.IncompleteReadError):
        return None


async def _get_rematch(reader: asyncio.StreamReader) -> bool:
    msg = await _recv(reader)
    return msg is not None and msg.get("type") == "rematch" and msg.get("accept") is True


async def _relay_game(
    reader1: asyncio.StreamReader,
    writer1: asyncio.StreamWriter,
    name1: str,
    reader2: asyncio.StreamReader,
    writer2: asyncio.StreamWriter,
    name2: str,
) -> None:
    tokens = ["X", "O"]
    random.shuffle(tokens)
    first = random.randint(1, 2)

    readers = {1: reader1, 2: reader2}
    writers = {1: writer1, 2: writer2}
    names = {1: name1, 2: name2}

    while True:
        await _send(writer1, {"type": "start", "token": tokens[0], "your_turn": first == 1, "opponent_name": name2})
        await _send(writer2, {"type": "start", "token": tokens[1], "your_turn": first == 2, "opponent_name": name1})
        print(f"Round started: {name1} vs {name2}. {names[first]} goes first.")

        # Relay moves until game over or disconnect
        current = first
        disconnected = False
        while True:
            other = 3 - current
            try:
                line = await readers[current].readline()
                if not line:
                    raise ConnectionResetError
                msg = json.loads(line.decode().strip())
            except Exception:
                print(f"{names[current]} disconnected.")
                try:
                    await _send(writers[other], {"type": "opponent_disconnected"})
                except Exception:
                    pass
                disconnected = True
                break

            if msg.get("type") == "game_over":
                print(f"Game over: {name1} vs {name2}.")
                break

            try:
                await _send(writers[other], msg)
            except Exception:
                print(f"{names[other]} disconnected.")
                try:
                    await _send(writers[current], {"type": "opponent_disconnected"})
                except Exception:
                    pass
                disconnected = True
                break

            current = other

        if disconnected:
            break

        # Wait for both players to respond to rematch prompt
        results = await asyncio.gather(
            _get_rematch(reader1),
            _get_rematch(reader2),
            return_exceptions=True,
        )
        both_accept = all(r is True for r in results)

        if both_accept:
            first = 3 - first  # flip who goes first
        else:
            try:
                await _send(writer1, {"type": "rematch_declined"})
            except Exception:
                pass
            try:
                await _send(writer2, {"type": "rematch_declined"})
            except Exception:
                pass
            break

    for w in (writer1, writer2):
        try:
            w.close()
            await w.wait_closed()
        except Exception:
            pass


async def _handle_client(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    global _waiting
    addr = writer.get_extra_info("peername")
    print(f"Connection from {addr}")

    msg = await _recv(reader)
    if msg is None or msg.get("type") != "name":
        writer.close()
        return
    name = msg["name"].strip() or "Opponent"

    async with _lock:
        if _waiting is None:
            _waiting = (reader, writer, name)
            partner = None
        else:
            partner = _waiting
            _waiting = None

    if partner is None:
        await _send(writer, {"type": "waiting"})
        print(f"{name} is waiting for an opponent...")
    else:
        reader1, writer1, name1 = partner
        asyncio.create_task(_relay_game(reader1, writer1, name1, reader, writer, name))


async def main() -> None:
    server = await asyncio.start_server(_handle_client, HOST, PORT)
    print(f"Server listening on {HOST}:{PORT}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import json
import sys

from game import ConnectFour

# ── Update these after deploying server.py ────────────────────────────────────
HOST = "caboose.proxy.rlwy.net"  # TCP hostname from Railway dashboard
PORT = 30828                     # TCP port from Railway dashboard
# ─────────────────────────────────────────────────────────────────────────────


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


async def _get_column(game: ConnectFour) -> int:
    loop = asyncio.get_running_loop()
    while True:
        try:
            raw = await loop.run_in_executor(None, input, f"Column (0-{game.COLS - 1}): ")
            col = int(raw.strip())
        except ValueError:
            print("Please enter a number.")
            continue
        if game.is_valid_move(col):
            return col
        print(f"Column {col} is not available. Try another.")


async def main() -> None:
    print(f"Connecting to {HOST}:{PORT}...")
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
    except OSError as e:
        print(f"Could not connect: {e}")
        sys.exit(1)

    loop = asyncio.get_running_loop()
    my_name = await loop.run_in_executor(None, input, "Your name: ")
    await _send(writer, {"type": "name", "name": my_name.strip() or "Anonymous"})

    # Wait for server handshake — may receive "waiting" before "start"
    while True:
        msg = await _recv(reader)
        if msg is None:
            print("Server closed the connection.")
            sys.exit(1)
        if msg["type"] == "waiting":
            print("Connected! Waiting for your opponent to join...")
        elif msg["type"] == "start":
            break

    my_token: str = msg["token"]
    your_turn: bool = msg["your_turn"]
    opponent_name: str = msg["opponent_name"]
    opponent_token = "O" if my_token == "X" else "X"
    print(f"Opponent: {opponent_name}")

    game = ConnectFour()

    while not game.game_over:
        if your_turn:
            game.print_board(my_token)
            col = await _get_column(game)
            game.play(my_token, col)
            await _send(writer, {"type": "move", "col": col})
            if game.game_over:
                await _send(writer, {"type": "game_over"})
        else:
            game.print_board(None)
            print(f"Waiting for {opponent_name}'s move...")
            incoming = await _recv(reader)
            if incoming is None or incoming.get("type") == "opponent_disconnected":
                game.print_board()
                print("Opponent disconnected. You win by default!")
                writer.close()
                return
            game.play(opponent_token, incoming["col"])

        your_turn = not your_turn

    game.print_board()
    if game.tied:
        print("It's a tie!")
    elif game.winner == my_token:
        print("You win!")
    else:
        print("Opponent wins!")

    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())

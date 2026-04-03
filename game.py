class ConnectFour:
    ROWS = 6
    COLS = 7

    def __init__(self):
        self.board = [[""] * self.COLS for _ in range(self.ROWS)]
        self.winner: str | None = None
        self.tied = False

    @property
    def game_over(self) -> bool:
        return self.winner is not None or self.tied

    def print_board(self, current_token: str | None = None) -> None:
        print("\033[H\033[J", end="")
        if current_token is not None:
            print(f"Your turn — Player {self._colored(current_token)}")
        else:
            print()
        print("  " + "   ".join(str(i) for i in range(self.COLS)))
        print("+" + "---+" * self.COLS)
        for row in self.board:
            cells = [self._colored(c) if c else " " for c in row]
            print("| " + " | ".join(cells) + " |")
            print("+" + "---+" * self.COLS)
        print()

    def _colored(self, token: str) -> str:
        if token == "X":
            return "\033[91mX\033[0m"
        if token == "O":
            return "\033[94mO\033[0m"
        return token

    def is_valid_move(self, col: int) -> bool:
        return 0 <= col < self.COLS and self.board[0][col] == ""

    def play(self, token: str, col: int) -> None:
        for r in range(self.ROWS - 1, -1, -1):
            if self.board[r][col] == "":
                self.board[r][col] = token
                self._update_state(token, r, col)
                return

    def _update_state(self, token: str, r: int, c: int) -> None:
        if self._check_win(token, r, c):
            self.winner = token
        elif self._board_full():
            self.tied = True

    def _board_full(self) -> bool:
        return all(self.board[0][c] != "" for c in range(self.COLS))

    def _check_win(self, token: str, r: int, c: int) -> bool:
        return (
            self._four_in_row(token, r, c)
            or self._four_in_col(token, r, c)
            or self._four_in_diag(token, r, c, dc=1)
            or self._four_in_diag(token, r, c, dc=-1)
        )

    def _four_in_row(self, token: str, r: int, c: int) -> bool:
        s = ""
        for j in range(c - 3, c + 4):
            if 0 <= j < self.COLS:
                s += token if self.board[r][j] == token else " "
        return token * 4 in s

    def _four_in_col(self, token: str, r: int, c: int) -> bool:
        # Pieces fall downward, so the topmost piece in a vertical 4-in-a-row
        # is always placed last. Check the 4 cells at rows r..r+3.
        s = ""
        for i in range(r + 3, r - 1, -1):
            if 0 <= i < self.ROWS:
                if self.board[i][c] == token:
                    s += token
        return s == token * 4

    def _four_in_diag(self, token: str, r: int, c: int, dc: int) -> bool:
        # dc=1: top-left → bottom-right diagonal
        # dc=-1: top-right → bottom-left diagonal
        s = ""
        col = c - 3 * dc
        for row in range(r - 3, r + 4):
            if 0 <= row < self.ROWS and 0 <= col < self.COLS:
                s += token if self.board[row][col] == token else " "
            col += dc
        return token * 4 in s

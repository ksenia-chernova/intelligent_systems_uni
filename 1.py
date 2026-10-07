import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Константы фигур
EMPTY = 0
WK = 1   # Белый король
BK = 2   # Черный король
WQ = 3   # Белый ферзь
WR = 4   # Белая ладья
WB = 5   # Белый слон
WN = 6   # Белый конь

PIECE_NAMES = {WQ: "Ферзь", WR: "Ладья", WB: "Слон", WN: "Конь"}
PIECE_SYMBOLS = {WK: "♔", BK: "♚", WQ: "♕", WR: "♖", WB: "♗", WN: "♘"}


class ChessBoard:
    """Представление шахматной доски 8x8"""
    
    def __init__(self):
        self.board = [[EMPTY] * 8 for _ in range(8)]
    
    def copy(self):
        new_board = ChessBoard()
        new_board.board = [row[:] for row in self.board]
        return new_board
    
    def place(self, row, col, piece):
        self.board[row][col] = piece
    
    def get(self, row, col):
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return -1
    
    def find_king(self, color):
        target = WK if color == 'white' else BK
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == target:
                    return (r, c)
        return None
    
    def is_path_clear(self, from_r, from_c, to_r, to_c):
        """Проверка чистоты пути для скользящих фигур"""
        dr = 0 if to_r == from_r else (1 if to_r > from_r else -1)
        dc = 0 if to_c == from_c else (1 if to_c > from_c else -1)
        r, c = from_r + dr, from_c + dc
        while (r, c) != (to_r, to_c):
            if self.board[r][c] != EMPTY:
                return False
            r += dr
            c += dc
        return True
    
    def can_piece_attack(self, from_r, from_c, to_r, to_c, piece):
        """Может ли фигура атаковать клетку"""
        dr = to_r - from_r
        dc = to_c - from_c
        
        if piece == WN:
            return (abs(dr), abs(dc)) in [(1, 2), (2, 1)]
        
        if piece == WK:
            return abs(dr) <= 1 and abs(dc) <= 1 and (dr, dc) != (0, 0)
        
        if piece in [WQ, WR]:
            if (dr == 0 or dc == 0) and (dr != 0 or dc != 0):
                if self.is_path_clear(from_r, from_c, to_r, to_c):
                    return True
        
        if piece in [WQ, WB]:
            if abs(dr) == abs(dc) and dr != 0:
                if self.is_path_clear(from_r, from_c, to_r, to_c):
                    return True
        
        return False
    
    def is_square_attacked_by_white(self, row, col):
        """Атакована ли клетка белыми фигурами"""
        wk = self.find_king('white')
        if wk:
            kr, kc = wk
            if abs(kr - row) <= 1 and abs(kc - col) <= 1 and (kr, kc) != (row, col):
                return True
        
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece in [WQ, WR, WB, WN]:
                    if self.can_piece_attack(r, c, row, col, piece):
                        return True
        return False
    
    def get_black_king_moves(self):
        """Все легальные ходы черного короля"""
        bk = self.find_king('black')
        if bk is None:
            return []
        kr, kc = bk
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue    
                nr, nc = kr + dr, kc + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if not self.is_square_attacked_by_white(nr, nc):
                        target = self.board[nr][nc]
                        if target not in [WK, WQ, WR, WB, WN]:
                            moves.append((nr, nc))
        return moves
    
    def is_in_check(self):
        """Шах черному королю?"""
        bk = self.find_king('black')
        if bk is None:
            return False
        return self.is_square_attacked_by_white(bk[0], bk[1])
    
    def is_checkmate(self):
        """Мат?"""
        return self.is_in_check() and len(self.get_black_king_moves()) == 0
    
    def is_stalemate(self):
        """Пат?"""
        return not self.is_in_check() and len(self.get_black_king_moves()) == 0


def find_solutions(bk_row, bk_col, piece1_type, piece2_type, progress_callback=None):
    """Поиск всех матовых/патовых позиций"""
    solutions = []
    total = 0
    same_pieces = (piece1_type == piece2_type)
    
    for wk_r in range(8):
        for wk_c in range(8):
            if (wk_r, wk_c) == (bk_row, bk_col):
                continue
            if abs(wk_r - bk_row) <= 1 and abs(wk_c - bk_col) <= 1:
                continue  # Короли не могут стоять рядом
            
            for p1_r in range(8):
                for p1_c in range(8):
                    if (p1_r, p1_c) == (bk_row, bk_col):
                        continue
                    if (p1_r, p1_c) == (wk_r, wk_c):
                        continue
                    
                    p2_start_r = p1_r if same_pieces else 0
                    p2_start_c = (p1_c + 1) if (same_pieces and p2_start_r == p1_r) else 0
                    
                    for p2_r in range(p2_start_r, 8):
                        start_c = p2_start_c if p2_r == p2_start_r else 0
                        for p2_c in range(start_c, 8):
                            if (p2_r, p2_c) == (bk_row, bk_col):
                                continue
                            if (p2_r, p2_c) == (wk_r, wk_c):
                                continue
                            if (p2_r, p2_c) == (p1_r, p1_c):
                                continue
                            
                            total += 1
                            if total % 5000 == 0 and progress_callback:
                                progress_callback(total)
                            
                            board = ChessBoard()
                            board.place(bk_row, bk_col, BK)
                            board.place(wk_r, wk_c, WK)
                            board.place(p1_r, p1_c, piece1_type)
                            board.place(p2_r, p2_c, piece2_type)
                            
                            if board.is_checkmate():
                                solutions.append(('Мат', board.copy()))
                            elif board.is_stalemate():
                                solutions.append(('Пат', board.copy()))
    
    return solutions


class ChessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа 1: Шахматы - матовые и патовые ситуации")
        self.root.geometry("950x750")
        self.root.resizable(True, True)
        
        self.solutions = []
        self.current_solution = 0
        self.searching = False
        
        self.create_widgets()
    
    def create_widgets(self):
        # Панель управления
        control_frame = ttk.LabelFrame(self.root, text="Параметры поиска", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Позиция черного короля
        ttk.Label(control_frame, text="Позиция черного короля:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        row_frame = ttk.Frame(control_frame)
        row_frame.grid(row=0, column=1, columnspan=4, sticky=tk.W)
        
        ttk.Label(row_frame, text="Горизонталь (1-8):").pack(side=tk.LEFT)
        self.bk_row_var = tk.IntVar(value=4)
        ttk.Spinbox(row_frame, from_=1, to=8, textvariable=self.bk_row_var, width=4).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row_frame, text="Вертикаль (a-h):").pack(side=tk.LEFT, padx=(15, 0))
        self.bk_col_var = tk.StringVar(value="d")
        col_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        self.bk_col_combo = ttk.Combobox(row_frame, textvariable=self.bk_col_var, 
                                          values=col_names, width=4, state='readonly')
        self.bk_col_combo.set("d")
        self.bk_col_combo.pack(side=tk.LEFT, padx=5)
        
        # Выбор фигур
        ttk.Label(control_frame, text="Фигура 1:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.piece1_var = tk.StringVar(value="Ферзь")
        ttk.Combobox(control_frame, textvariable=self.piece1_var,
                     values=["Ферзь", "Ладья", "Слон", "Конь"], width=12, state='readonly').grid(row=1, column=1, padx=5)
        
        ttk.Label(control_frame, text="Фигура 2:").grid(row=1, column=2, sticky=tk.W, padx=5)
        self.piece2_var = tk.StringVar(value="Ладья")
        ttk.Combobox(control_frame, textvariable=self.piece2_var,
                     values=["Ферзь", "Ладья", "Слон", "Конь"], width=12, state='readonly').grid(row=1, column=3, padx=5)
        
        # Кнопка поиска
        self.find_btn = ttk.Button(control_frame, text="🔍 Найти комбинации", command=self.start_search)
        self.find_btn.grid(row=2, column=0, columnspan=2, pady=10, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹ Остановить", command=self.stop_search, state=tk.DISABLED)
        self.stop_btn.grid(row=2, column=2, columnspan=2, pady=10, padx=5)
        
        self.status_label = ttk.Label(control_frame, text="Готов к поиску")
        self.status_label.grid(row=2, column=4, columnspan=2, padx=10)
        
        # Прогресс-бар
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate', length=200)
        self.progress.grid(row=3, column=0, columnspan=6, sticky=tk.EW, pady=5)
        
        # Панель навигации
        nav_frame = ttk.LabelFrame(self.root, text="Навигация по решениям", padding=10)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(nav_frame, text="⏮ Первая", command=self.first_solution).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="◀ Предыдущая", command=self.prev_solution).pack(side=tk.LEFT, padx=5)
        
        self.solution_label = ttk.Label(nav_frame, text="Комбинация: 0 / 0", font=("Arial", 11, "bold"))
        self.solution_label.pack(side=tk.LEFT, padx=20)
        
        ttk.Button(nav_frame, text="Следующая ▶", command=self.next_solution).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Последняя ", command=self.last_solution).pack(side=tk.LEFT, padx=5)
        
        self.type_label = ttk.Label(nav_frame, text="Тип: —", font=("Arial", 11))
        self.type_label.pack(side=tk.RIGHT, padx=20)
        
        # Переход к конкретной комбинации
        goto_frame = ttk.Frame(nav_frame)
        goto_frame.pack(side=tk.RIGHT, padx=10)
        ttk.Label(goto_frame, text="Перейти к №:").pack(side=tk.LEFT)
        self.goto_var = tk.StringVar()
        ttk.Entry(goto_frame, textvariable=self.goto_var, width=6).pack(side=tk.LEFT, padx=3)
        ttk.Button(goto_frame, text="OK", command=self.goto_solution).pack(side=tk.LEFT)
        
        # Шахматная доска
        board_frame = ttk.Frame(self.root)
        board_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        
        self.canvas = tk.Canvas(board_frame, width=560, height=560, bg='white')
        self.canvas.pack(expand=True)
        
        self.draw_empty_board()
        
        # Информация
        info_frame = ttk.Frame(self.root)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(info_frame, 
                  text="Условия: черный король фиксирован, белый король + 2 фигуры создают мат/пат",
                  font=("Arial", 9), foreground='gray').pack()
    
    def draw_empty_board(self):
        self.canvas.delete("all")
        cell_size = 65
        offset = 25
        
        for r in range(8):
            for c in range(8):
                x = offset + c * cell_size
                y = offset + r * cell_size
                color = "#F0D9B5" if (r + c) % 2 == 0 else "#B58863"
                self.canvas.create_rectangle(x, y, x + cell_size, y + cell_size, fill=color, outline='black')
        
        # Координаты
        col_labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        for i in range(8):
            self.canvas.create_text(offset + i * cell_size + cell_size // 2, offset - 12,
                                   text=col_labels[i], font=("Arial", 10, "bold"))
            self.canvas.create_text(offset - 15, offset + i * cell_size + cell_size // 2,
                                   text=str(8 - i), font=("Arial", 10, "bold"))
    
    def draw_board(self, board):
        self.canvas.delete("all")
        cell_size = 65
        offset = 25
        
        for r in range(8):
            for c in range(8):
                x = offset + c * cell_size
                y = offset + r * cell_size
                color = "#F0D9B5" if (r + c) % 2 == 0 else "#B58863"
                self.canvas.create_rectangle(x, y, x + cell_size, y + cell_size, fill=color, outline='black')
        
        # Координаты
        col_labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        for i in range(8):
            self.canvas.create_text(offset + i * cell_size + cell_size // 2, offset - 12,
                                   text=col_labels[i], font=("Arial", 10, "bold"))
            self.canvas.create_text(offset - 15, offset + i * cell_size + cell_size // 2,
                                   text=str(8 - i), font=("Arial", 10, "bold"))
        
        # Фигуры
        for r in range(8):
            for c in range(8):
                piece = board.board[r][c]
                if piece != EMPTY:
                    x = offset + c * cell_size + cell_size // 2
                    y = offset + r * cell_size + cell_size // 2
                    symbol = PIECE_SYMBOLS.get(piece, "?")
                    color = "white" if piece in [WK, WQ, WR, WB, WN] else "black"
                    self.canvas.create_text(x, y, text=symbol, font=("Arial", 36), fill=color)
        
        # Подсветка черного короля
        bk = board.find_king('black')
        if bk:
            kr, kc = bk
            x = offset + kc * cell_size
            y = offset + kr * cell_size
            self.canvas.create_rectangle(x + 2, y + 2, x + cell_size - 2, y + cell_size - 2,
                                         outline='red', width=3)
    
    def start_search(self):
        if self.searching:
            return
        
        bk_row = 8 - self.bk_row_var.get()  # Преобразование: ряд 1 = индекс 7
        bk_col = ord(self.bk_col_var.get()) - ord('a') # Колонка a = индекс 0
        
        piece_map = {"Ферзь": WQ, "Ладья": WR, "Слон": WB, "Конь": WN}
        p1 = piece_map[self.piece1_var.get()]
        p2 = piece_map[self.piece2_var.get()]
        
        self.searching = True
        self.find_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.start()
        self.status_label.config(text="Поиск...")
        self.solutions = []
        self.current_solution = 0
        
        # Запуск поиска в отдельном потоке
        thread = threading.Thread(target=self._search_thread, 
                                  args=(bk_row, bk_col, p1, p2), daemon=True)
        thread.start()
    
    def _search_thread(self, bk_row, bk_col, p1, p2):
        try:
            self.solutions = find_solutions(bk_row, bk_col, p1, p2)
            self.root.after(0, self._search_complete)
        except Exception as e:
            self.root.after(0, lambda: self._search_error(str(e)))
    
    def _search_complete(self):
        self.searching = False
        self.find_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress.stop()
        
        if self.solutions:
            self.status_label.config(text=f"✅ Найдено: {len(self.solutions)} комбинаций")
            self.show_solution(0)
        else:
            self.status_label.config(text="❌ Комбинации не найдены для данных параметров")
            self.draw_empty_board()
            self.solution_label.config(text="Комбинация: 0 / 0")
            self.type_label.config(text="Тип: —")
    
    def _search_error(self, error):
        self.searching = False
        self.find_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress.stop()
        self.status_label.config(text=f"Ошибка: {error}")
        messagebox.showerror("Ошибка", f"Произошла ошибка при поиске:\n{error}")
    
    def stop_search(self):
        self.searching = False
        self.find_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress.stop()
        self.status_label.config(text="Поиск остановлен пользователем")
    
    def show_solution(self, idx):
        if 0 <= idx < len(self.solutions):
            self.current_solution = idx
            sol_type, board = self.solutions[idx]
            self.draw_board(board)
            self.solution_label.config(text=f"Комбинация: {idx + 1} / {len(self.solutions)}")
            color = "red" if sol_type == "Мат" else "blue"
            self.type_label.config(text=f"Тип: {sol_type}", foreground=color)
    
    def first_solution(self):
        if self.solutions:
            self.show_solution(0)
    
    def prev_solution(self):
        if self.current_solution > 0:
            self.show_solution(self.current_solution - 1)
    
    def next_solution(self):
        if self.current_solution < len(self.solutions) - 1:
            self.show_solution(self.current_solution + 1)
    
    def last_solution(self):
        if self.solutions:
            self.show_solution(len(self.solutions) - 1)
    
    def goto_solution(self):
        try:
            idx = int(self.goto_var.get()) - 1
            if 0 <= idx < len(self.solutions):
                self.show_solution(idx)
            else:
                messagebox.showwarning("Внимание", f"Введите число от 1 до {len(self.solutions)}")
        except ValueError:
            messagebox.showwarning("Внимание", "Введите корректное число")


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessApp(root)
    root.mainloop()
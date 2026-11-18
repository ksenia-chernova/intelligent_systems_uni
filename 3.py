import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

# Настройка темы
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class KnightTourApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Задача о ходе коня (Поиск нескольких решений)")
        self.geometry("1250x750")
        self.resizable(False, False)

        # Параметры
        self.n = 6  # строки (уменьшил дефолт для безопасности)
        self.m = 6  # столбцы
        self.start_row = 0
        self.start_col = 0
        
        self.all_paths = []          # Список всех найденных путей
        self.current_solution_idx = 0 # Индекс текущего отображаемого решения
        
        self.solution_found = False
        self.animation_running = False
        self.current_step = 0

        # Ходы коня
        self.moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]

        self._build_ui()

    def _build_ui(self):
        # ===== Верхняя панель управления =====
        control_frame = ctk.CTkFrame(self, corner_radius=10)
        control_frame.pack(padx=15, pady=10, fill="x")

        # Размер доски
        ctk.CTkLabel(control_frame, text="Размер доски:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=10, pady=8, sticky="w")

        ctk.CTkLabel(control_frame, text="Строки (n):").grid(row=0, column=1, padx=5, pady=5)
        self.entry_n = ctk.CTkEntry(control_frame, width=60)
        self.entry_n.insert(0, "6")
        self.entry_n.grid(row=0, column=2, padx=5, pady=5)

        ctk.CTkLabel(control_frame, text="Столбцы (m):").grid(row=0, column=3, padx=5, pady=5)
        self.entry_m = ctk.CTkEntry(control_frame, width=60)
        self.entry_m.insert(0, "6")
        self.entry_m.grid(row=0, column=4, padx=5, pady=5)

        # Начальная позиция
        ctk.CTkLabel(control_frame, text="Начальная позиция:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=5, padx=15, pady=8, sticky="w")

        ctk.CTkLabel(control_frame, text="Строка:").grid(row=0, column=6, padx=5, pady=5)
        self.entry_row = ctk.CTkEntry(control_frame, width=60)
        self.entry_row.insert(0, "0")
        self.entry_row.grid(row=0, column=7, padx=5, pady=5)

        ctk.CTkLabel(control_frame, text="Столбец:").grid(row=0, column=8, padx=5, pady=5)
        self.entry_col = ctk.CTkEntry(control_frame, width=60)
        self.entry_col.insert(0, "0")
        self.entry_col.grid(row=0, column=9, padx=5, pady=5)

        # Кнопки управления
        btn_frame = ctk.CTkFrame(self, corner_radius=10)
        btn_frame.pack(padx=15, pady=5, fill="x")

        self.btn_solve = ctk.CTkButton(btn_frame, text="🔍 Найти решения", command=self._on_solve, width=160, height=35, font=ctk.CTkFont(size=13, weight="bold"))
        self.btn_solve.pack(side="left", padx=10, pady=8)

        self.btn_prev_sol = ctk.CTkButton(btn_frame, text="⏮ Пред. решение", command=self._prev_solution, width=140, height=35, state="disabled")
        self.btn_prev_sol.pack(side="left", padx=5, pady=8)

        self.btn_next_sol = ctk.CTkButton(btn_frame, text="След. решение ⏭", command=self._next_solution, width=140, height=35, state="disabled")
        self.btn_next_sol.pack(side="left", padx=5, pady=8)

        self.btn_animate = ctk.CTkButton(btn_frame, text="▶ Анимация", command=self._on_animate, width=120, height=35, state="disabled")
        self.btn_animate.pack(side="left", padx=10, pady=8)

        self.btn_reset = ctk.CTkButton(btn_frame, text="🔄 Сброс", command=self._on_reset, width=100, height=35)
        self.btn_reset.pack(side="left", padx=10, pady=8)

        # Скорость анимации
        ctk.CTkLabel(btn_frame, text="Скорость (мс):").pack(side="right", padx=10, pady=8)
        self.entry_speed = ctk.CTkEntry(btn_frame, width=70)
        self.entry_speed.insert(0, "100")
        self.entry_speed.pack(side="right", padx=5, pady=8)

        self.solution_count_label = ctk.CTkLabel(btn_frame, text="Найдено: 0", font=ctk.CTkFont(size=13, weight="bold"), text_color="green")
        self.solution_count_label.pack(side="right", padx=10, pady=8)

        # Статус
        self.status_label = ctk.CTkLabel(btn_frame, text="Статус: Ожидание...", font=ctk.CTkFont(size=12, weight="bold"))
        self.status_label.pack(side="right", padx=15, pady=8)

        # ===== Canvas для доски =====
        canvas_frame = ctk.CTkFrame(self, corner_radius=10)
        canvas_frame.pack(padx=15, pady=10, fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        self._draw_board()

    def _on_canvas_resize(self, event):
        self._draw_board()

    def _get_cell_size(self):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        cell_w = canvas_width // self.m
        cell_h = canvas_height // self.n
        return min(cell_w, cell_h, 60)

    def _draw_board(self, highlight_path=False):
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width < 10 or canvas_height < 10:
            return

        cell_size = self._get_cell_size()
        board_w = cell_size * self.m
        board_h = cell_size * self.n
        offset_x = (canvas_width - board_w) // 2
        offset_y = (canvas_height - board_h) // 2

        # Рисуем клетки
        for r in range(self.n):
            for c in range(self.m):
                x = offset_x + c * cell_size
                y = offset_y + r * cell_size

                if (r + c) % 2 == 0:
                    color = "#f0d9b5"
                else:
                    color = "#b58863"

                self.canvas.create_rectangle(x, y, x + cell_size, y + cell_size, fill=color, outline="#555", width=1)
                self.canvas.create_text(x + cell_size // 2, y + cell_size // 2,
                                        text=f"{r},{c}", font=("Arial", 7), fill="#888")

        # Определяем, какой путь рисовать
        current_path = []
        if self.all_paths and 0 <= self.current_solution_idx < len(self.all_paths):
            current_path = self.all_paths[self.current_solution_idx]

        # Подсветка пути
        if highlight_path and current_path:
            # Рисуем весь путь полупрозрачным
            for i, (r, c) in enumerate(current_path):
                x = offset_x + c * cell_size
                y = offset_y + r * cell_size
                alpha = 0.3 + 0.7 * (i / max(len(current_path) - 1, 1))
                color = f"#{int(50*alpha):02x}{int(150*alpha):02x}{int(255*alpha):02x}"
                self.canvas.create_rectangle(x + 2, y + 2, x + cell_size - 2, y + cell_size - 2,
                                             fill=color, outline="")
                self.canvas.create_text(x + cell_size // 2, y + cell_size // 2,
                                        text=str(i + 1), font=("Arial", 9, "bold"), fill="white")

        # Рисуем коня на текущем шаге анимации или в конце пути
        if current_path:
            if highlight_path and self.current_step < len(current_path):
                r, c = current_path[self.current_step]
            else:
                r, c = current_path[-1]

            x = offset_x + c * cell_size
            y = offset_y + r * cell_size

            self.canvas.create_oval(x + 4, y + 4, x + cell_size - 4, y + cell_size - 4,
                                    fill="#e74c3c", outline="#c0392b", width=2)
            self.canvas.create_text(x + cell_size // 2, y + cell_size // 2,
                                    text="♞", font=("Arial", int(cell_size * 0.5)), fill="white")

    def _on_canvas_click(self, event):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        cell_size = self._get_cell_size()
        board_w = cell_size * self.m
        board_h = cell_size * self.n
        offset_x = (canvas_width - board_w) // 2
        offset_y = (canvas_height - board_h) // 2

        col = (event.x - offset_x) // cell_size
        row = (event.y - offset_y) // cell_size

        if 0 <= row < self.n and 0 <= col < self.m:
            self.entry_row.delete(0, "end")
            self.entry_row.insert(0, str(row))
            self.entry_col.delete(0, "end")
            self.entry_col.insert(0, str(col))
            self._draw_board()

    def _read_params(self):
        try:
            self.n = int(self.entry_n.get())
            self.m = int(self.entry_m.get())
            self.start_row = int(self.entry_row.get())
            self.start_col = int(self.entry_col.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные целые числа!")
            return False

        if self.n < 1 or self.m < 1:
            messagebox.showerror("Ошибка", "Размер доски должен быть >= 1!")
            return False
        if self.n > 8 or self.m > 8:
            messagebox.showwarning("Предупреждение", "Размер более 8x8 может вызвать зависание при поиске нескольких решений!")
        if not (0 <= self.start_row < self.n) or not (0 <= self.start_col < self.m):
            messagebox.showerror("Ошибка", "Начальная позиция вне доски!")
            return False

        return True

    def _on_solve(self):
        if not self._read_params():
            return

        self.status_label.configure(text="Статус: Вычисление...", text_color="yellow")
        self.solution_count_label.configure(text="Найдено: ...")
        self.update_idletasks() # Обновляем UI, чтобы текст успел отобразиться

        self.all_paths = []
        self.current_solution_idx = 0
        self.current_step = 0
        self.solution_found = False

        # Запуск алгоритма
        result = self._solve_backtrack()

        if result and len(self.all_paths) > 0:
            self.solution_count_label.configure(text=str(len(self.all_paths)))

            self.solution_found = True
            self.btn_animate.configure(state="normal")
            
            self._update_nav_buttons()
            self._draw_board(highlight_path=True)
        else:
            self.solution_count_label.configure(text="0")
            self.status_label.configure(text="Статус: Решение не найдено!", text_color="red")
            messagebox.showinfo("Результат", f"Для доски {self.n}×{self.m} из позиции ({self.start_row}, {self.start_col}) решения не найдены.")

    def _solve_backtrack(self):
        """Поиск с возвратом (Backtracking) + эвристика Варнсдорфа для ускорения."""
        board = [[-1] * self.m for _ in range(self.n)]
        
        # Вложенная функция для подсчёта степени клетки (для сортировки ходов)
        def get_degree(r, c):
            degree = 0
            for dr, dc in self.moves:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.n and 0 <= nc < self.m and board[nr][nc] == -1:
                    degree += 1
            return degree

        def backtrack(r, c, step, path):
            
            # Если сделали N*M ходов, путь найден
            if step == self.n * self.m:
                self.all_paths.append(list(path))
                return
            
            # Собираем все возможные следующие ходы
            next_moves = []
            for dr, dc in self.moves:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.n and 0 <= nc < self.m and board[nr][nc] == -1:
                    deg = get_degree(nr, nc)
                    next_moves.append((deg, nr, nc))
            
            # Сортируем по степени (эвристика Варнсдорфа): сначала клетки с наименьшим числом выходов
            # Это позволяет найти первое решение мгновенно и значительно ускоряет перебор остальных
            next_moves.sort(key=lambda x: x[0])
            
            for deg, nr, nc in next_moves:
                board[nr][nc] = step
                path.append((nr, nc))
                
                backtrack(nr, nc, step + 1, path)
                
                # Откат (Backtracking)
                board[nr][nc] = -1
                path.pop()

        # Инициализация
        board[self.start_row][self.start_col] = 0
        backtrack(self.start_row, self.start_col, 1, [(self.start_row, self.start_col)])
        
        return len(self.all_paths) > 0

    def _update_nav_buttons(self):
        """Обновляет состояние кнопок навигации по решениям."""
        if len(self.all_paths) > 1:
            self.btn_prev_sol.configure(state="normal")
            self.btn_next_sol.configure(state="normal")
        else:
            self.btn_prev_sol.configure(state="disabled")
            self.btn_next_sol.configure(state="disabled")

    def _prev_solution(self):
        if not self.solution_found or len(self.all_paths) <= 1:
            return
        self.current_solution_idx = (self.current_solution_idx - 1) % len(self.all_paths)
        self.current_step = 0
        self._draw_board(highlight_path=True)
        self.status_label.configure(text=f"Статус: Решение {self.current_solution_idx + 1} из {len(self.all_paths)}", text_color="cyan")

    def _next_solution(self):
        if not self.solution_found or len(self.all_paths) <= 1:
            return
        self.current_solution_idx = (self.current_solution_idx + 1) % len(self.all_paths)
        self.current_step = 0
        self._draw_board(highlight_path=True)
        self.status_label.configure(text=f"Статус: Решение {self.current_solution_idx + 1} из {len(self.all_paths)}", text_color="cyan")

    def _on_animate(self):
        if not self.solution_found or self.animation_running:
            return
        self.animation_running = True
        self.current_step = 0
        self._animate_step()

    def _animate_step(self):
        if not self.animation_running:
            return
        
        current_path = self.all_paths[self.current_solution_idx]
        if self.current_step < len(current_path):
            self._draw_board(highlight_path=True)
            self.status_label.configure(text=f"Статус: Решение {self.current_solution_idx + 1}, Ход {self.current_step + 1}/{len(current_path)}", text_color="cyan")
            self.current_step += 1
            try:
                speed = int(self.entry_speed.get())
            except ValueError:
                speed = 100
            self.after(speed, self._animate_step)
        else:
            self.animation_running = False
            self.status_label.configure(text="Статус: Анимация завершена!", text_color="green")
            self._draw_board(highlight_path=True)

    def _on_reset(self):
        self.animation_running = False
        self.all_paths = []
        self.current_solution_idx = 0
        self.current_step = 0
        self.solution_found = False
        self.solution_count_label.configure(text="0")
        self.btn_animate.configure(state="disabled")
        self.btn_prev_sol.configure(state="disabled")
        self.btn_next_sol.configure(state="disabled")
        self.status_label.configure(text="Статус: Сброшено", text_color="gray")
        self._draw_board()


if __name__ == "__main__":
    app = KnightTourApp()
    app.mainloop()
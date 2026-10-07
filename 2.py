import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque

# ============================================================
#  Конфигурация лабиринтов
#  0 – проход (чёрный), 1 – стена (белый),
#  7 – выход (красный), 9 – вход (синий)
# ============================================================

MAP1 = [
    [1, 1, 0, 0, 0, 0, 1, 1, 9, 1],
    [7, 0, 0, 1, 1, 0, 1, 0, 0, 1],
    [1, 1, 1, 1, 1, 0, 1, 0, 1, 0],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 1, 0, 1, 0, 1, 1, 0, 1],
    [0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 0, 1, 1, 1, 1],
    [0, 1, 1, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 1, 1, 1, 0, 1],
    [1, 9, 1, 0, 0, 0, 0, 1, 9, 1],
]

MAP2 = [
    [7, 0, 0, 0, 0, 0, 0, 0, 0, 9],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 0, 1, 0, 1, 0],
    [0, 1, 0, 0, 0, 0, 1, 0, 1, 0],
    [0, 1, 0, 0, 0, 0, 1, 1, 1, 0],
    [0, 1, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 1, 1, 0, 0, 0, 0, 1, 1, 0],
    [0, 1, 1, 0, 0, 0, 1, 0, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 0, 1, 0],
    [0, 0, 0, 9, 0, 0, 0, 0, 0, 0],
]

CELL_SIZE = 50  # размер ячейки в пикселях


# ============================================================
#  Класс MazeApp
# ============================================================
class MazeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабиринт – поиск кратчайшего пути")
        self.root.resizable(False, False)

        self.maps = {"MAP1": MAP1, "MAP2": MAP2}
        self.current_map_name = "MAP1"
        self.current_map = [row[:] for row in MAP1]

        self.paths = []          # список всех найденных путей
        self.shortest_path = []  # кратчайший путь
        self.current_path_idx = -1  # индекс отображаемого пути

        self._build_ui()
        self._find_all_paths()
        self._draw_maze()

    # --------------------------------------------------------
    #  Построение интерфейса
    # --------------------------------------------------------
    def _build_ui(self):
        # Панель управления
        control_frame = ttk.Frame(self.root, padding=8)
        control_frame.pack(fill=tk.X)

        ttk.Label(control_frame, text="Лабиринт:").pack(side=tk.LEFT)
        self.map_var = tk.StringVar(value="MAP1")
        map_combo = ttk.Combobox(
            control_frame, textvariable=self.map_var,
            values=list(self.maps.keys()), state="readonly", width=10
        )
        map_combo.pack(side=tk.LEFT, padx=5)
        map_combo.bind("<<ComboboxSelected>>", self._on_map_change)

        ttk.Button(control_frame, text="Найти пути",
                   command=self._find_all_paths).pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Кратчайший",
                   command=self._show_shortest).pack(side=tk.LEFT, padx=5)

        # Навигация по маршрутам
        nav_frame = ttk.Frame(self.root, padding=8)
        nav_frame.pack(fill=tk.X)

        ttk.Button(nav_frame, text="◀ Пред.",
                   command=self._prev_path).pack(side=tk.LEFT, padx=3)
        ttk.Button(nav_frame, text="След. ▶",
                   command=self._next_path).pack(side=tk.LEFT, padx=3)

        ttk.Label(nav_frame, text="Маршрут:").pack(side=tk.LEFT, padx=(15, 3))
        self.path_idx_var = tk.StringVar(value="-")
        idx_spin = ttk.Spinbox(
            nav_frame, textvariable=self.path_idx_var,
            from_=1, to=1, width=5, command=self._on_spin
        )
        self.idx_spin = idx_spin
        idx_spin.pack(side=tk.LEFT, padx=3)

        # Информационная панель
        self.info_var = tk.StringVar(value="Нажмите «Найти пути»")
        ttk.Label(self.root, textvariable=self.info_var,
                  font=("Arial", 10)).pack(pady=4)

        # Холст для отрисовки
        width = len(self.current_map[0]) * CELL_SIZE
        height = len(self.current_map) * CELL_SIZE
        self.canvas = tk.Canvas(
            self.root, width=width, height=height, bg="white"
        )
        self.canvas.pack(padx=10, pady=10)

    # --------------------------------------------------------
    #  Поиск всех путей (BFS по всем возможным маршрутам)
    # --------------------------------------------------------
    def _find_all_paths(self):
        maze = self.current_map
        rows, cols = len(maze), len(maze[0])

        # Найти вход (9) и выходы (7)
        start = None
        exits = []
        for r in range(rows):
            for c in range(cols):
                if maze[r][c] == 9:
                    start = (r, c)
                elif maze[r][c] == 7:
                    exits.append((r, c))

        if start is None:
            messagebox.showwarning("Ошибка", "Вход (9) не найден!")
            return
        if not exits:
            messagebox.showwarning("Ошибка", "Выходы (7) не найдены!")
            return

        # DFS для поиска всех простых путей
        all_paths = []
        visited = set()

        def dfs(r, c, path):
            if (r, c) in exits:
                all_paths.append(path[:])
                return
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if (nr, nc) not in visited and maze[nr][nc] != 1:
                        visited.add((nr, nc))
                        path.append((nr, nc))
                        dfs(nr, nc, path)
                        path.pop()
                        visited.remove((nr, nc))

        visited.add(start)
        dfs(start[0], start[1], [start])

        self.paths = all_paths
        if all_paths:
            self.shortest_path = min(all_paths, key=len)
        else:
            self.shortest_path = []

        # Обновить UI
        info = f"Найдено маршрутов: {len(all_paths)}"
        if all_paths:
            lengths = sorted(set(len(p) for p in all_paths))
            info += f" | Длины: {lengths} | Кратчайший: {len(self.shortest_path)} ячеек"
        self.info_var.set(info)

        self.path_idx_var.set("1")
        self.idx_spin.config(to=max(1, len(all_paths)))
        self.current_path_idx = 0 if all_paths else -1

        self._draw_maze()

    # --------------------------------------------------------
    #  Отрисовка лабиринта
    # --------------------------------------------------------
    def _draw_maze(self):
        self.canvas.delete("all")
        maze = self.current_map
        rows, cols = len(maze), len(maze[0])

        # Рисуем ячейки
        for r in range(rows):
            for c in range(cols):
                x1, y1 = c * CELL_SIZE, r * CELL_SIZE
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
                val = maze[r][c]

                if val == 1:
                    color = "white"   # стена
                elif val == 9:
                    color = "blue"    # вход
                elif val == 7:
                    color = "red"     # выход
                else:
                    color = "black"   # проход

                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="gray"
                )

        # Рисуем текущий маршрут
        path_to_draw = None
        if self.paths and 0 <= self.current_path_idx < len(self.paths):
            path_to_draw = self.paths[self.current_path_idx]
        elif self.shortest_path:
            path_to_draw = self.shortest_path

        if path_to_draw and len(path_to_draw) > 1:
            # Зелёная ломаная линия по центрам ячеек
            points = []
            for (r, c) in path_to_draw:
                cx = c * CELL_SIZE + CELL_SIZE // 2
                cy = r * CELL_SIZE + CELL_SIZE // 2
                points.extend([cx, cy])
            self.canvas.create_line(
                *points, fill="lime", width=4, capstyle=tk.ROUND
            )

    # --------------------------------------------------------
    #  Обработчики событий
    # --------------------------------------------------------
    def _on_map_change(self, event=None):
        name = self.map_var.get()
        self.current_map_name = name
        self.current_map = [row[:] for row in self.maps[name]]
        self._find_all_paths()

    def _show_shortest(self):
        if self.shortest_path:
            self.current_path_idx = -1  # спец. значение = кратчайший
            self.path_idx_var.set("min")
            self._draw_maze()
            self.info_var.set(
                f"Кратчайший путь: длина = {len(self.shortest_path)} ячеек"
            )

    def _prev_path(self):
        if not self.paths:
            return
        self.current_path_idx = (self.current_path_idx - 1) % len(self.paths)
        self.path_idx_var.set(str(self.current_path_idx + 1))
        self._draw_maze()
        p = self.paths[self.current_path_idx]
        self.info_var.set(
            f"Маршрут {self.current_path_idx + 1}/{len(self.paths)}, "
            f"длина = {len(p)}"
        )

    def _next_path(self):
        if not self.paths:
            return
        self.current_path_idx = (self.current_path_idx + 1) % len(self.paths)
        self.path_idx_var.set(str(self.current_path_idx + 1))
        self._draw_maze()
        p = self.paths[self.current_path_idx]
        self.info_var.set(
            f"Маршрут {self.current_path_idx + 1}/{len(self.paths)}, "
            f"длина = {len(p)}"
        )

    def _on_spin(self):
        try:
            idx = int(self.path_idx_var.get()) - 1
            if 0 <= idx < len(self.paths):
                self.current_path_idx = idx
                self._draw_maze()
                p = self.paths[self.current_path_idx]
                self.info_var.set(
                    f"Маршрут {idx + 1}/{len(self.paths)}, длина = {len(p)}"
                )
        except ValueError:
            pass


# ============================================================
#  Запуск
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = MazeApp(root)
    root.mainloop()
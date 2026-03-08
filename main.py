import heapq
import math
import time
import random
from abc import ABC, abstractmethod
from collections import deque
import tkinter as tk
from tkinter import ttk, messagebox


# ==========================================
#  DOMAIN MODEL (Encapsulation)
# ==========================================

class PuzzleState:
    """Represents a node in the search tree. Immutable board state."""
    GOAL = (0, 1, 2, 3, 4, 5, 6, 7, 8)

    def __init__(self, board: tuple, parent=None, move: str = None, depth: int = 0):
        self._board = tuple(board)
        self._parent = parent
        self._move = move
        self._depth = depth

    @property
    def board(self) -> tuple:
        return self._board

    @property
    def depth(self) -> int:
        return self._depth

    @property
    def move(self) -> str:
        return self._move

    @property
    def parent(self):
        return self._parent

    def is_goal(self) -> bool:
        return self._board == self.GOAL

    def get_neighbors(self) -> list:
        neighbors = []
        zero_index = self._board.index(0)
        row, col = zero_index // 3, zero_index % 3

        directions = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}

        for direction, (d_row, d_col) in directions.items():
            new_row, new_col = row + d_row, col + d_col
            if 0 <= new_row <= 2 and 0 <= new_col <= 2:
                new_index = new_row * 3 + new_col
                new_board = list(self._board)
                # Swap
                new_board[zero_index], new_board[new_index] = new_board[new_index], new_board[zero_index]
                
                child_state = PuzzleState(
                    board=new_board,
                    parent=self,
                    move=direction,
                    depth=self._depth + 1
                )
                neighbors.append(child_state)
        return neighbors

    def get_path_to_state(self) -> tuple:
        """Backtracks to root to formulate the path and sequence of states."""
        moves, states = [], []
        current = self
        while current is not None:
            states.append(current.board)
            if current.move is not None:
                moves.append(current.move)
            current = current.parent
        moves.reverse()
        states.reverse()
        return moves, states


# ==========================================
#  STRATEGY PATTERN For Heuristics
# ==========================================

class HeuristicStrategy(ABC):
    @abstractmethod
    def calculate(self, board: tuple) -> float:
        pass
#h = abs(current cell:x - goal:x) + abs(current cell:y - goal:y) where x is rows and y is columns in our code
class ManhattanHeuristic(HeuristicStrategy):
    def calculate(self, board: tuple) -> float:
        total = 0
        for index, tile in enumerate(board):
            if tile == 0: continue
            cur_row, cur_col = index // 3, index % 3
            goal_row, goal_col = tile // 3, tile % 3
            total += abs(cur_row - goal_row) + abs(cur_col - goal_col)
        return total


#h = sqrt((current cell:x - goal:x)2 + (current cell.y - goal:y)2) 
class EuclideanHeuristic(HeuristicStrategy):
    def calculate(self, board: tuple) -> float:
        total = 0.0
        for index, tile in enumerate(board):
            if tile == 0: continue
            cur_row, cur_col = index // 3, index % 3
            goal_row, goal_col = tile // 3, tile % 3
            total += math.sqrt((cur_row - goal_row) ** 2 + (cur_col - goal_col) ** 2)
        return total


# ==========================================
#  STRATEGY PATTERN For Search Algorithms
# ==========================================

class SearchStrategy(ABC):
    """Interface for all search algorithms."""
    
    @abstractmethod
    def search(self, start_state: PuzzleState) -> dict:
        pass

    def _build_result(self, goal_state: PuzzleState, nodes_expanded: int, start_time: float) -> dict:
        """Helper for standardizing the return payload."""
        running_time = time.time() - start_time
        path_to_goal, states = goal_state.get_path_to_state()
        return {
            "path_to_goal": path_to_goal,
            "cost_of_path": len(path_to_goal),
            "nodes_expanded": nodes_expanded,
            "search_depth": goal_state.depth,
            "running_time": running_time,
            "states": states,
        }

class BFSSearch(SearchStrategy):
    def search(self, start_state: PuzzleState) -> dict:
        start_time = time.time()
        frontier = deque([start_state])
        frontier_boards = {start_state.board}
        explored = set()
        nodes_expanded = 0

        while frontier:
            current = frontier.popleft()
            frontier_boards.remove(current.board)
            explored.add(current.board)

            if current.is_goal():
                return self._build_result(current, nodes_expanded, start_time)

            nodes_expanded += 1
            for neighbor in current.get_neighbors():
                if neighbor.board not in frontier_boards and neighbor.board not in explored:
                    frontier.append(neighbor)
                    frontier_boards.add(neighbor.board)
        return None

class DFSSearch(SearchStrategy):
    def search(self, start_state: PuzzleState) -> dict:
        start_time = time.time()
        frontier = [start_state]
        frontier_boards = {start_state.board}
        explored = set()
        nodes_expanded = 0

        while frontier:
            current = frontier.pop()
            frontier_boards.remove(current.board)
            explored.add(current.board)

            if current.is_goal():
                return self._build_result(current, nodes_expanded, start_time)

            nodes_expanded += 1
            # Reverse for conventional order execution
            for neighbor in reversed(current.get_neighbors()):
                if neighbor.board not in frontier_boards and neighbor.board not in explored:
                    frontier.append(neighbor)
                    frontier_boards.add(neighbor.board)
        return None

class IterativeDeepeningDFS(SearchStrategy):
    def search(self, start_state: PuzzleState) -> dict:
        start_time = time.time()
        nodes_expanded = 0

        # Depth limit is 50 loops because the maximum optimal 8-puzzle depth is 31 
        for depth_limit in range(50):
            frontier = [start_state]
            explored = {} 
            while frontier:
                current = frontier.pop()
                if current.is_goal():
                    return self._build_result(current, nodes_expanded, start_time)

                if current.depth < depth_limit:
                    explored[current.board] = current.depth
                    nodes_expanded += 1
                    for neighbor in reversed(current.get_neighbors()):
                        if neighbor.board not in explored or neighbor.depth < explored[neighbor.board]:
                            frontier.append(neighbor)
        return None

class AStarSearch(SearchStrategy):
    def __init__(self, heuristic: HeuristicStrategy):
        self.heuristic = heuristic

    def search(self, start_state: PuzzleState) -> dict:
        start_time = time.time()
        counter = 0
        h0 = self.heuristic.calculate(start_state.board)
        heap = [(h0, counter, start_state)]
        frontier_map = {start_state.board: h0}

        explored = set()
        nodes_expanded = 0

        while heap:
            f, _, current = heapq.heappop(heap)

            if current.board in explored: continue
            if current.board in frontier_map and f > frontier_map[current.board]: continue
            explored.add(current.board)

            if current.is_goal():
                return self._build_result(current, nodes_expanded, start_time)

            nodes_expanded += 1
            for neighbor in current.get_neighbors():
                if neighbor.board in explored: continue
                
                f_new = neighbor.depth + self.heuristic.calculate(neighbor.board)
                if neighbor.board not in frontier_map or f_new < frontier_map[neighbor.board]:
                    frontier_map[neighbor.board] = f_new
                    counter += 1
                    heapq.heappush(heap, (f_new, counter, neighbor))
        return None


# ==========================================
#  FACTORY PATTERN
# ==========================================

class SearchAlgorithmFactory:
    """Creates and wires the correct Search Strategy based on UI input."""
    
    @staticmethod
    def create_solver(algorithm_name: str) -> SearchStrategy:
        if algorithm_name == "BFS":
            return BFSSearch()
        elif algorithm_name == "DFS":
            return DFSSearch()
        elif algorithm_name == "Iterative DFS":
            return IterativeDeepeningDFS()
        elif algorithm_name == "A* (Manhattan)":
            return AStarSearch(ManhattanHeuristic())
        elif algorithm_name == "A* (Euclidean)":
            return AStarSearch(EuclideanHeuristic())
        else:
            raise ValueError(f"Unknown Algorithm: {algorithm_name}")


# ==========================================
#  UTILITIES
# ==========================================

class PuzzleUtils:
    @staticmethod
    def is_solvable(board: tuple) -> bool:
        """ check to verify if the puzzle state is solvable."""
        inversions = 0
        tiles = [n for n in board if n != 0]
        for i in range(len(tiles)):
            for j in range(i + 1, len(tiles)):
                if tiles[i] > tiles[j]:
                    inversions += 1
        return inversions % 2 == 0

    @staticmethod
    def generate_random_solvable_state() -> tuple:
        """Generates a random state that is guaranteed to be solvable."""
        while True:
            base_state = list(range(9))
            random.shuffle(base_state)
            if PuzzleUtils.is_solvable(base_state):
                return tuple(base_state)


# ==========================================
#  GUI (View & Controller)
# ==========================================

class PuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("8-Puzzle Solver Toolkit - Advanced MVC")
        self.root.resizable(False, False)
        
        # Color Palette
        self.bg_color = "#f0f2f5"
        self.board_bg = "#34495e"
        self.tile_color = "#ecf0f1"
        self.tile_text_color = "#2c3e50"
        self.empty_color = "#bdc3c7"
        self.goal_color = "#2ecc71"
        
        self.root.configure(bg=self.bg_color)

        # UI State
        self.solution_states = []
        self.path_to_goal = []
        self.current_step = 0
        self.is_animating = False

        self._build_gui()

    def _build_gui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # --- Control Panel Frame ---
        control_frame = tk.Frame(self.root, bg=self.bg_color, pady=10)
        control_frame.pack(fill=tk.X, padx=20)

        tk.Label(control_frame, text="Initial State:", bg=self.bg_color, font=("Helvetica", 11, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.state_entry = ttk.Entry(control_frame, width=20, font=("Helvetica", 11))
        self.state_entry.grid(row=0, column=1, padx=10, pady=5)
        self.state_entry.insert(0, "1,2,5,3,4,0,6,7,8")

        self.shuffle_btn = tk.Button(control_frame, text="Shuffle", command=self.shuffle_board, bg="#2196F3", fg="white", font=("Helvetica", 9, "bold"), relief="flat", cursor="hand2")
        self.shuffle_btn.grid(row=0, column=2, padx=5, pady=5)

        tk.Label(control_frame, text="Algorithm:", bg=self.bg_color, font=("Helvetica", 11, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.algo_var = tk.StringVar()
        self.algo_dropdown = ttk.Combobox(control_frame, textvariable=self.algo_var, state="readonly", width=18, font=("Helvetica", 10))
        self.algo_dropdown['values'] = ("BFS", "DFS", "Iterative DFS", "A* (Manhattan)", "A* (Euclidean)")
        self.algo_dropdown.current(3) 
        self.algo_dropdown.grid(row=1, column=1, padx=10, pady=5)

        self.solve_btn = tk.Button(control_frame, text="SOLVE PUZZLE", command=self.run_solver, bg="#4CAF50", fg="white", font=("Helvetica", 11, "bold"), relief="flat", cursor="hand2")
        self.solve_btn.grid(row=0, column=3, rowspan=2, padx=15, sticky=tk.NSEW, pady=5)

        # --- Stats Frame ---
        self.stats_frame = tk.LabelFrame(self.root, text=" Search Results ", bg=self.bg_color, font=("Helvetica", 10, "bold"), padx=15, pady=10)
        self.stats_frame.pack(fill=tk.X, padx=20, pady=5)

        self.stats_label = tk.Label(self.stats_frame, text="Awaiting input...", bg=self.bg_color, justify=tk.LEFT, font=("Courier", 10))
        self.stats_label.pack(anchor=tk.W)

        # Sliding Path Components
        self.path_toggle_btn = tk.Button(self.stats_frame, text="Show Path to Goal", command=self.toggle_path, state=tk.DISABLED, relief="groove", font=("Helvetica", 9), bg="#e0e0e0", cursor="hand2")
        self.path_toggle_btn.pack(anchor=tk.W, pady=(10, 0))

        self.path_frame = tk.Frame(self.stats_frame, bg=self.bg_color)
        self.path_text = tk.Text(self.path_frame, height=3, width=50, wrap=tk.WORD, font=("Courier", 10), state=tk.DISABLED, relief="flat", bg="#ffffff")
        self.path_scroll = ttk.Scrollbar(self.path_frame, command=self.path_text.yview)
        self.path_text.config(yscrollcommand=self.path_scroll.set)
        
        self.path_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        self.path_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # --- Visualizer Frame ---
        self.viz_container = tk.Frame(self.root, bg=self.bg_color, pady=10)
        self.viz_container.pack()

        self.info_label = tk.Label(self.viz_container, text="Step 0: Ready", font=("Helvetica", 14, "bold"), bg=self.bg_color, fg="#333333")
        self.info_label.pack(pady=(0, 10))

        # The actual board backing
        self.board_frame = tk.Frame(self.viz_container, bg=self.board_bg, padx=8, pady=8, relief="sunken", borderwidth=4)
        self.board_frame.pack()

        self.tiles = []
        for r in range(3):
            row_tiles = []
            for c in range(3):
                lbl = tk.Label(self.board_frame, text="", width=3, height=1, font=("Helvetica", 36, "bold"), relief="raised", borderwidth=2)
                lbl.grid(row=r, column=c, padx=3, pady=3)
                row_tiles.append(lbl)
            self.tiles.append(row_tiles)

        btn_frame = tk.Frame(self.viz_container, bg=self.bg_color, pady=15)
        btn_frame.pack()
        
        self.prev_btn = tk.Button(btn_frame, text="◀ Previous", command=self.prev_step, state=tk.DISABLED, width=10, font=("Helvetica", 10, "bold"), bg="#95a5a6", fg="white", relief="flat", cursor="hand2")
        self.prev_btn.pack(side=tk.LEFT, padx=10)

        # Auto-play button
        self.play_btn = tk.Button(btn_frame, text="▶ Auto-Play", command=self.toggle_animation, state=tk.DISABLED, width=12, font=("Helvetica", 10, "bold"), bg="#e67e22", fg="white", relief="flat", cursor="hand2")
        self.play_btn.pack(side=tk.LEFT, padx=10)

        self.next_btn = tk.Button(btn_frame, text="Next ▶", command=self.next_step, state=tk.DISABLED, width=10, font=("Helvetica", 10, "bold"), bg="#95a5a6", fg="white", relief="flat", cursor="hand2")
        self.next_btn.pack(side=tk.RIGHT, padx=10)
        
        self.draw_board((1, 2, 5, 3, 4, 0, 6, 7, 8))

    # --- UI Controller Methods ---

    def toggle_path(self):
        if self.path_frame.winfo_ismapped():
            self.path_frame.pack_forget()
            self.path_toggle_btn.config(text="Show Path to Goal")
        else:
            self.path_frame.pack(fill=tk.X, pady=(5, 0))
            self.path_toggle_btn.config(text="Hide Path to Goal")

    def shuffle_board(self):
        self.stop_animation()
        
        new_board = PuzzleUtils.generate_random_solvable_state()
        self.state_entry.delete(0, tk.END)
        self.state_entry.insert(0, ",".join(str(x) for x in new_board))
        self.draw_board(new_board)
        
        self.info_label.config(text="Random State Generated", fg="#e67e22")
        self.stats_label.config(text="Awaiting input...", fg="#333333")
        
        if self.path_frame.winfo_ismapped(): self.toggle_path()
        self.path_toggle_btn.config(state=tk.DISABLED)
        
        self.solution_states = [] 
        self.prev_btn.config(state=tk.DISABLED, bg="#95a5a6")
        self.next_btn.config(state=tk.DISABLED, bg="#95a5a6")
        self.play_btn.config(state=tk.DISABLED, bg="#95a5a6")

    def run_solver(self):
        self.stop_animation()
        
        raw_text = self.state_entry.get().strip()
        try:
            parts = raw_text.split(",")
            board = tuple(int(x) for x in parts)
            if len(board) != 9 or set(board) != set(range(9)): raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Must be 9 comma-separated numbers from 0 to 8.")
            return

        if not PuzzleUtils.is_solvable(board):
            messagebox.showerror("Unsolvable State", "This puzzle state is mathematically impossible to solve! Please enter a valid state or click Shuffle.")
            return

        if self.path_frame.winfo_ismapped(): self.toggle_path()
        self.path_toggle_btn.config(state=tk.DISABLED)

        algo_choice = self.algo_var.get()
        start_state = PuzzleState(board)
        solver = SearchAlgorithmFactory.create_solver(algo_choice)

        self.stats_label.config(text=f"Solving with {algo_choice}... Please wait.", fg="#2980b9")
        self.root.update() 

        result = solver.search(start_state)

        if not result:
            self.stats_label.config(text="No solution found or search exhausted.", fg="#c0392b")
            return

        stats_text = (
            f"Cost of Path: {result['cost_of_path']}\n"
            f"Nodes Expanded: {result['nodes_expanded']}\n"
            f"Search Depth: {result['search_depth']}\n"
            f"Running Time: {result['running_time']:.5f} sec"
        )
        self.stats_label.config(text=stats_text, fg="#333333")

        path_str = ", ".join(result["path_to_goal"]) if result["path_to_goal"] else "None (Already at Goal)"
        self.path_text.config(state=tk.NORMAL)
        self.path_text.delete(1.0, tk.END)
        self.path_text.insert(tk.END, path_str)
        self.path_text.config(state=tk.DISABLED)
        self.path_toggle_btn.config(state=tk.NORMAL)

        self.solution_states = result["states"]
        self.path_to_goal = result["path_to_goal"]
        self.current_step = 0
        self.update_viz()

    def update_viz(self):
        self.draw_board(self.solution_states[self.current_step])
        
        # Check if we are at the goal
        is_goal = (self.current_step == len(self.solution_states) - 1) and len(self.solution_states) > 0
        
        if self.current_step == 0:
            self.info_label.config(text="Step 0: Initial State", fg="#333333")
        elif is_goal:
            move = self.path_to_goal[self.current_step - 1]
            self.info_label.config(text=f"Step {self.current_step}: Move {move} (GOAL REACHED!)", fg=self.goal_color)
        else:
            move = self.path_to_goal[self.current_step - 1]
            self.info_label.config(text=f"Step {self.current_step}: Move {move}", fg="#333333")

        # Color the board green if goal is reached
        for r in range(3):
            for c in range(3):
                if is_goal and self.solution_states[self.current_step][r * 3 + c] != 0:
                    self.tiles[r][c].config(bg=self.goal_color, fg="white")

        # Handle Button States and Colors
        if self.current_step > 0:
            self.prev_btn.config(state=tk.NORMAL, bg="#34495e")
        else:
            self.prev_btn.config(state=tk.DISABLED, bg="#95a5a6")
            
        if self.current_step < len(self.solution_states) - 1:
            self.next_btn.config(state=tk.NORMAL, bg="#34495e")
            self.play_btn.config(state=tk.NORMAL, bg="#e67e22")
        else:
            self.next_btn.config(state=tk.DISABLED, bg="#95a5a6")
            self.play_btn.config(state=tk.DISABLED, bg="#95a5a6")
            self.stop_animation() 

    def draw_board(self, board):
        for r in range(3):
            for c in range(3):
                val = board[r * 3 + c]
                text = str(val) if val != 0 else ""
                
                # Apply Tile Styling
                if val == 0:
                    self.tiles[r][c].config(text=text, bg=self.empty_color, relief="flat")
                else:
                    self.tiles[r][c].config(text=text, bg=self.tile_color, fg=self.tile_text_color, relief="raised")

    def prev_step(self):
        self.stop_animation()
        if self.current_step > 0:
            self.current_step -= 1
            self.update_viz()

    def next_step(self):
        self.stop_animation()
        if self.current_step < len(self.solution_states) - 1:
            self.current_step += 1
            self.update_viz()

    # --- Animation ---

    def toggle_animation(self):
        if self.is_animating:
            self.stop_animation()
        else:
            if self.current_step >= len(self.solution_states) - 1:
                self.current_step = 0
                self.update_viz()
            
            self.is_animating = True
            self.play_btn.config(text="Stop", bg="#c0392b")
            self.play_next_frame()

    def stop_animation(self):
        self.is_animating = False
        if len(self.solution_states) > 0 and self.current_step < len(self.solution_states) - 1:
            self.play_btn.config(text="Auto-Play", bg="#e67e22")

    def play_next_frame(self):
        if self.is_animating and self.current_step < len(self.solution_states) - 1:
            self.current_step += 1
            self.update_viz()
            self.root.after(300, self.play_next_frame)

if __name__ == "__main__":
    root = tk.Tk()
    app = PuzzleApp(root)
    root.mainloop()

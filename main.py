from collections import deque
import time
import tracemalloc


class PuzzleState:
    GOAL = (0, 1, 2, 3, 4, 5, 6, 7, 8)

    def __init__(self, board, parent=None, move=None, depth=0):
        self.board = tuple(board)
        self.parent = parent
        self.move = move
        self.depth = depth

    def is_goal(self):
        if self.board == PuzzleState.GOAL:
            return True
        else:
            return False

    def print_board(self):
        print(self.board[0], self.board[1], self.board[2])
        print(self.board[3], self.board[4], self.board[5])
        print(self.board[6], self.board[7], self.board[8])
        print()

    def make_move(self, direction):
        zero_index = self.board.index(0)

        row = zero_index // 3
        col = zero_index % 3

        new_row = row
        new_col = col

        if direction == "Up":
            new_row = row - 1
        elif direction == "Down":
            new_row = row + 1
        elif direction == "Left":
            new_col = col - 1
        elif direction == "Right":
            new_col = col + 1
        else:
            return None

        if new_row < 0 or new_row > 2 or new_col < 0 or new_col > 2:
            return None

        new_index = new_row * 3 + new_col

        new_board = list(self.board)

        temp = new_board[zero_index]
        new_board[zero_index] = new_board[new_index]
        new_board[new_index] = temp

        child_state = PuzzleState(
            board=new_board,
            parent=self,
            move=direction,
            depth=self.depth + 1
        )

        return child_state

    def get_neighbors(self):
        neighbors = []

        up_state = self.make_move("Up")
        if up_state is not None:
            neighbors.append(up_state)

        down_state = self.make_move("Down")
        if down_state is not None:
            neighbors.append(down_state)

        left_state = self.make_move("Left")
        if left_state is not None:
            neighbors.append(left_state)

        right_state = self.make_move("Right")
        if right_state is not None:
            neighbors.append(right_state)

        return neighbors

    def get_path(self):
        moves = []
        states = []

        current = self

        while current is not None:
            states.append(current.board)

            if current.move is not None:
                moves.append(current.move)

            current = current.parent

        moves.reverse()
        states.reverse()

        return moves, states


class BFSSearch:
    def solve(self, start_state):
        tracemalloc.start()
        start_time = time.time()

        frontier = deque()
        frontier.append(start_state)

        frontier_boards = set()
        frontier_boards.add(start_state.board)

        explored = set()

        nodes_expanded = 0
        max_fringe_size = 1
        max_search_depth = 0

        while len(frontier) > 0:
            current_state = frontier.popleft()
            frontier_boards.remove(current_state.board)

            explored.add(current_state.board)

            if current_state.is_goal():
                running_time = time.time() - start_time
                current_mem, peak_mem = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                return self.build_result(
                    goal_state=current_state,
                    nodes_expanded=nodes_expanded,
                    fringe_size=len(frontier),
                    max_fringe_size=max_fringe_size,
                    max_search_depth=max_search_depth,
                    running_time=running_time,
                    max_ram_usage=peak_mem / (1024 * 1024)
                )

            nodes_expanded = nodes_expanded + 1

            neighbors = current_state.get_neighbors()

            for neighbor in neighbors:
                if neighbor.board not in frontier_boards and neighbor.board not in explored:
                    frontier.append(neighbor)
                    frontier_boards.add(neighbor.board)

                    if neighbor.depth > max_search_depth:
                        max_search_depth = neighbor.depth

            if len(frontier) > max_fringe_size:
                max_fringe_size = len(frontier)

        running_time = time.time() - start_time
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return None

    def build_result(self, goal_state, nodes_expanded, fringe_size, max_fringe_size,
                     max_search_depth, running_time, max_ram_usage):
        path_to_goal, states = goal_state.get_path()

        result = {
            "path_to_goal": path_to_goal,
            "cost_of_path": len(path_to_goal),
            "nodes_expanded": nodes_expanded,
            "fringe_size": fringe_size,
            "max_fringe_size": max_fringe_size,
            "search_depth": goal_state.depth,
            "max_search_depth": max_search_depth,
            "running_time": running_time,
            "max_ram_usage": max_ram_usage,
            "states": states
        }

        return result


class PuzzleSolver:
    def __init__(self, strategy):
        self.strategy = strategy

    def set_strategy(self, strategy):
        self.strategy = strategy

    def solve(self, start_state):
        return self.strategy.solve(start_state)


def parse_state(text):
    parts = text.split(",")
    board = []

    for x in parts:
        board.append(int(x))

    board = tuple(board)

    if len(board) != 9:
        raise ValueError("Input must contain exactly 9 numbers.")

    if set(board) != set(range(9)):
        raise ValueError("Input must contain numbers from 0 to 8 exactly once.")

    return board





def show_result(result):
    if result is None:
        print("No solution found.")
        return

    print("path_to_goal:", result["path_to_goal"])
    print("cost_of_path:", result["cost_of_path"])
    print("nodes_expanded:", result["nodes_expanded"])
    print("fringe_size:", result["fringe_size"])
    print("max_fringe_size:", result["max_fringe_size"])
    print("search_depth:", result["search_depth"])
    print("max_search_depth:", result["max_search_depth"])
    print("running_time:", format(result["running_time"], ".8f"))
    print("max_ram_usage:", format(result["max_ram_usage"], ".8f"))
    print()

    print("Trace of states:")
    step_number = 0

    for board in result["states"]:
        print("Step", step_number)
        state = PuzzleState(board)
        state.print_board()
        step_number = step_number + 1

def main():
    text = input("Enter initial state like 1,2,5,3,4,0,6,7,8: ")
    board = parse_state(text)



    start_state = PuzzleState(board)

    bfs_strategy = BFSSearch()
    solver = PuzzleSolver(bfs_strategy)

    result = solver.solve(start_state)
    show_result(result)


if __name__ == "__main__":
    main()
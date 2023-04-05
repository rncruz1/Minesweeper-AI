# ==============================CS-199==================================
# FILE:			MyAI.py
#
# AUTHOR: 		Justin Chung
#
# DESCRIPTION:	This file contains the MyAI class. You will implement your
# 				agent in this file. You will write the 'getAction' function,
# 				the constructor, and any additional helper functions.
#
# NOTES: 		- MyAI inherits from the abstract AI class in AI.py.
#
# 				- DO NOT MAKE CHANGES TO THIS FILE.
# ==============================CS-199==================================

# Draft AI Requirements:
# Complete 30% out of N Beginner worlds (8x8 with 10mines) and 15% out of N Intermediate worlds (16x16 with 40 mines).

# Final AI Requirements:
# Complete 60% out of N Beginner worlds (8x8 with 10mines), 50% out of N Intermediate worlds (16x16 with 40 mines), and 10% out of N Expert worlds (16x30 with 99 mines)

from typing import Dict, FrozenSet, List, Set, Tuple
from collections import defaultdict
import traceback
from datetime import datetime, timedelta

from AI import AI
from Action import Action


COVERED = -100
FLAG = -200

SET_OF_SQUARES = Set[Tuple[int, int]]
SQUARE = Tuple[int, int]


class MyAI(AI):
    def __init__(
        self,
        rowDimension: int,
        colDimension: int,
        totalMines: int,
        startX: int,
        startY: int,
    ):

        self.rowCount = rowDimension
        self.colCount = colDimension
        self.totalMines = totalMines

        self.moves: SET_OF_SQUARES = set()

        self.uncovered_squares: SET_OF_SQUARES = set()
        self.uncovered_squares.add((startX, startY))

        self.bombs: SET_OF_SQUARES = set()
        self.flagged_bombs: SET_OF_SQUARES = set()

        self.prevMove: SQUARE = (startX, startY)

        self.board = [[COVERED] * rowDimension for _ in range(colDimension)]
        self.effective_label_board = [
            [COVERED] * rowDimension for _ in range(colDimension)
        ]

        self.all_possible_moves = {
            (x, y) for x in range(self.colCount) for y in range(self.rowCount)
        }

        self.round = 0

        self.cutoff_time = datetime.now()
        self.start_time = datetime.now()

    def update_effective_label_board(self):
        """
        Recomputes the effective label board
        """
        self.effective_label_board = [
            self.board[col].copy() for col in range(self.colCount)
        ]

        # Update the labels based off of known bombs
        for (bombX, bombY) in self.bombs:
            neighbors = self.get_neighbors(bombX, bombY)
            neighbors.intersection_update(self.uncovered_squares)

            for (x, y) in neighbors:
                self.effective_label_board[x][y] -= 1

    def get_all_covered_squares(self):
        return self.all_possible_moves.difference(self.uncovered_squares)

    def get_neighbors(self, posX, posY) -> SET_OF_SQUARES:
        neighbors = set()
        for x in range(posX - 1, posX + 2):
            for y in range(posY - 1, posY + 2):
                if self.rowCount > y >= 0 and self.colCount > x >= 0:
                    neighbors.add((x, y))

        neighbors.remove((posX, posY))

        return neighbors

    def get_helper_squares(self) -> Set[Tuple[int, int]]:
        covered_squares = self.get_all_covered_squares()

        helper_squares = set()
        for (x, y) in self.uncovered_squares:
            helper_squares.update(self.get_neighbors(x, y))

        return helper_squares.difference(covered_squares)

    def get_frontier_segment(
        self, frontier: SET_OF_SQUARES, startX: int, startY: int
    ) -> SET_OF_SQUARES:
        segment_squares: SET_OF_SQUARES = set()
        queue: List[Tuple[int, int]] = list()

        segment_squares.add((startX, startY))
        x, y = startX, startY
        queue.append((x, y))
        while len(queue) > 0:
            for square in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if square in frontier and not square in segment_squares:
                    segment_squares.add(square)
                    queue.append(square)
                    x, y = square
            else:
                x, y = queue.pop()

        return segment_squares

    def get_all_frontier_segments(self) -> List[SET_OF_SQUARES]:
        frontier = self.get_frontier_squares()
        segments: List[SET_OF_SQUARES] = list()
        while len(frontier) > 0:
            x, y = frontier.pop()
            segment = self.get_frontier_segment(frontier, x, y)
            frontier.difference_update(segment)
            segments.append(segment)

        return segments

    def get_all_uncovered_neighbors(self, squares: SET_OF_SQUARES) -> SET_OF_SQUARES:
        all_neighbors = set()
        for square in squares:
            all_neighbors.update(self.get_neighbors(square[0], square[1]))

        return all_neighbors.intersection(self.uncovered_squares)

    def get_all_covered_neighbors(self, squares: SET_OF_SQUARES) -> SET_OF_SQUARES:
        all_neighbors = set()
        for square in squares:
            all_neighbors.update(self.get_neighbors(square[0], square[1]))

        return all_neighbors.difference(self.uncovered_squares)

    def compute_distances(self, from_square: SQUARE, to: SET_OF_SQUARES):
        from_x, from_y = from_square

        distances = {}

        for (x, y) in to:
            distances[(x, y)] = (x - from_x) ** 2 + (y - from_y) ** 2

        return distances

    def get_start_square(self, frontier: SET_OF_SQUARES):
        visited = set()

        current_square = list(frontier)[0]

        while True:
            visited.add(current_square)
            other_frontier_squares = frontier.difference(visited)
            distances = self.compute_distances(current_square, other_frontier_squares)
            distances = {k: v for k, v in distances.items() if v <= 4}

            if len(distances) == 0:
                return current_square

            distances_sorted = sorted(distances.items(), key=lambda item: item[1])
            closest_square = distances_sorted[0][0]

            current_square = closest_square

    def get_depth_first_search_segments(self) -> List[SQUARE]:
        frontier_squares = self.get_frontier_squares()

        assert len(frontier_squares) > 0, "NO FRONTIER SQUARES!!!"

        start_square = list(frontier_squares)[0]
        current_path = [start_square]
        current_square = start_square

        visited_squares: SET_OF_SQUARES = set()

        while True:
            visited_squares.add(current_square)

            # Find next square to search
            other_frontier_squares = frontier_squares.difference(visited_squares)

            if len(other_frontier_squares) == 0:
                return current_path

            else:
                distances = self.compute_distances(
                    current_square, other_frontier_squares
                )

                distances_sorted = sorted(distances.items(), key=lambda item: item[1])
                closest_square = distances_sorted[0][0]

                current_path.append(closest_square)
                current_square = closest_square

    class CutoffTimeReached(Exception):
        pass

    def depth_search_child(
        self, effective_labels: Dict[SQUARE, int], path: List[SQUARE]
    ) -> Set[FrozenSet[SQUARE]]:
        """
        Pick whether root node is bomb or not
        Pass remaining path and effective labels to subproblem handler

        The subproblem handler will return any bomb combinations that are valid

        Parent only calls subproblem handler if parent's solution is not yet valid (i.e. need more bombs)
        If subproblem handler return empty set, it was unable to find valid solutions

        If root node *WAS* a bomb, flip to not bomb, and pass subpath and effective labels
        to subproblem handler again.
        """

        # Bail if we're taking too long
        if datetime.now() > self.cutoff_time:
            raise self.CutoffTimeReached()

        effective_labels_original = effective_labels.copy()

        if len(path) == 0:
            return set()
        elif len(path) == 1:
            # See if square can be bomb or not
            square = path[0]
            neighbors = self.get_neighbors(square[0], square[1])
            neighbors.intersection_update(self.uncovered_squares)

            # Parent should only call child if the solution requires more bombs
            assert not all(
                label == 0 for label in effective_labels.values()
            ), "Subproblem handler should NOT have been called by parent!"

            can_be_bomb = all(effective_labels[n] == 1 for n in neighbors) and all(
                v == 0 for k, v in effective_labels.items() if k not in neighbors
            )
            if can_be_bomb:
                return set((frozenset((square,)),))
            else:
                return set()
        else:
            root_square = path[0]
            valid_sets = set()

            # Check if root_square can be a bomb
            neighbors = self.get_neighbors(root_square[0], root_square[1])
            neighbors.intersection_update(self.uncovered_squares)

            can_be_bomb = not any(effective_labels[n] == 0 for n in neighbors)

            if can_be_bomb:
                # Can be bomb
                for n in neighbors:
                    effective_labels[n] -= 1

                # Check if current solution is valid
                if all(label == 0 for label in effective_labels.values()):
                    valid_sets.add(frozenset((root_square,)))
                else:
                    valid_sub_sets = self.depth_search_child(
                        effective_labels.copy(), path[1:]
                    )

                    for sub_set in valid_sub_sets:
                        valid_sets.add(frozenset((root_square, *sub_set)))

            valid_sets.update(
                self.depth_search_child(effective_labels_original.copy(), path[1:])
            )

            return valid_sets

    def depth_search_on_segment(self, search_path: List[SQUARE]):
        # print(f"{len(search_path)=}")
        search_path_set = set(search_path)

        effective_labels: Dict[SQUARE, int] = {}
        neighbors = self.get_all_uncovered_neighbors(set(search_path))
        for neighbor in neighbors:
            nx, ny = neighbor
            effective_labels[neighbor] = self.effective_label_board[nx][ny]

        seconds_to_run = len(search_path) + 3
        self.cutoff_time = datetime.now() + timedelta(0, seconds_to_run)

        valid_bomb_combinations = self.depth_search_child(
            effective_labels.copy(), search_path
        )

        # Remove combinations that are too big
        remaining_bombs = self.totalMines - len(self.bombs)
        valid_bomb_combinations = set(
            filter(lambda item: len(item) <= remaining_bombs, valid_bomb_combinations)
        )

        # Special Case where there's only one valid combination
        if len(valid_bomb_combinations) == 1:
            bombs = valid_bomb_combinations.pop()
            self.bombs.update(bombs)
            self.moves.update(search_path_set.difference(bombs))
            return

        # Get all squares that were bombs
        bomb_counts = defaultdict(lambda: 0)
        for comb in valid_bomb_combinations:
            for bomb in comb:
                bomb_counts[bomb] += 1

        not_bombs = search_path_set.difference(bomb_counts.keys())
        # not_bombs.difference_update(self.bombs)  # TODO: WTF???
        self.moves.update(not_bombs)

        if len(not_bombs) != 0:
            # print("Found Completely Safe Moves", not_bombs)
            return

        # Probability
        # print(f"{bomb_counts=}")

        best_move_count = min(bomb_counts.values())

        best_moves = list(
            filter(
                lambda item: item[1] == best_move_count,
                bomb_counts.items(),
            )
        )
        best_moves = [i[0] for i in best_moves]

        if len(best_moves) == 1:
            best_move = best_moves[0]
        else:
            covered_squares = self.get_all_covered_squares()
            best_moves.sort(
                key=lambda item: len(
                    # Maybe don't comb bombs
                    self.get_neighbors(item[0], item[1]).intersection(covered_squares)
                ),
                # reverse=True,
            )
            best_move = best_moves[0]

        # print(f"Playing Best Move, {best_move=}")
        self.moves.add(best_move)

    def depth_search(self):
        try:
            search_path = self.get_depth_first_search_segments()
        except AssertionError:
            # Do the guessing stuff instead
            return

        try:
            if len(search_path) < 40:
                self.depth_search_on_segment(search_path)
            else:
                raise self.CutoffTimeReached()
        except:
            # print("Lame Probability")
            counts = {s: self.calculate_probability(s) for s in search_path}
            min_square = min(counts.items(), key=lambda t: t[0])
            self.moves.add(min_square[0])

    def get_frontier_squares(self) -> SET_OF_SQUARES:
        frontier = set()

        for (x, y) in self.uncovered_squares:
            neighbors = self.get_neighbors(x, y)
            frontier.update(neighbors)

        frontier.difference_update(self.uncovered_squares)
        frontier.difference_update(self.bombs)
        return frontier

    def find_valid_moves(self):
        zero_tiles = {
            (x, y)
            for x in range(self.colCount)
            for y in range(self.rowCount)
            if self.effective_label_board[x][y] == 0
        }

        moves_to_make = set()
        for (x, y) in zero_tiles:
            neighbors = self.get_neighbors(x, y)
            moves_to_make.update(neighbors)

        moves_to_make.difference_update(self.uncovered_squares)
        self.moves.update(moves_to_make)

    def mark_guaranteed_squares(self):
        changes_made = True

        while changes_made:
            changes_made = False
            covered_squares = self.get_all_covered_squares()

            for (x, y) in self.uncovered_squares:
                neighbors = self.get_neighbors(x, y)
                covered_neighbors = neighbors.intersection(covered_squares)
                covered_neighbors.difference_update(self.bombs)

                if len(covered_neighbors) == 0:
                    continue

                if len(covered_neighbors) == self.effective_label_board[x][y]:
                    changes_made = True
                    self.bombs.update(covered_neighbors)

                    self.update_effective_label_board()

                if self.effective_label_board[x][y] == 0:
                    neighbors = self.get_neighbors(x, y)
                    squares_to_mark = neighbors.difference(self.uncovered_squares)
                    squares_to_mark.difference_update(self.bombs)
                    self.moves.update(squares_to_mark)

        # If we've found all bombs then everything else is safe
        # This is stupid, but we can't leave early :(
        if len(self.bombs) == self.totalMines:
            # print("Found all bombs, making all other moves!")
            self.moves.update(self.get_all_covered_squares().difference(self.bombs))

    def mark_zero_squares(self, number: int):
        if number == 0:
            prevX, prevY = self.prevMove

            for (x, y) in self.get_neighbors(prevX, prevY):
                if (x, y) not in self.uncovered_squares:
                    self.moves.add((x, y))

    def get_flag_action(self):
        if len(self.bombs) != len(self.flagged_bombs):
            bombs_to_be_flagged = self.bombs.difference(self.flagged_bombs)
            x, y = bombs_to_be_flagged.pop()
            self.prevMove = (x, y)
            self.flagged_bombs.add((x, y))
            return Action(AI.Action.FLAG, x, y)
        else:
            return None

    def calculate_probability(self, square: SQUARE):
        posX, posY = square

        count = 0

        neighbors = self.get_neighbors(posX, posY)
        neighbors.intersection_update(self.uncovered_squares)
        for x, y in neighbors:
            hint = self.effective_label_board[x][y]
            count += hint

        return count

    def check_world_solved(self):
        return (
            len(self.uncovered_squares)
            == self.colCount * self.rowCount - self.totalMines
        )

    def get_next_move(self) -> Action:
        if len(self.moves) > 0:
            move = self.moves.pop()
            self.prevMove = move
            self.uncovered_squares.add(move)
            return Action(AI.Action.UNCOVER, move[0], move[1])

        # print("MOVE FALL THROUGH!")
        return Action(AI.Action.LEAVE)

    def getAction(self, number: int) -> Action:
        try:
            # print("Round: ", self.round)
            # print("MOVES TO MAKE: ", self.moves)
            self.round += 1

            if self.check_world_solved():
                return Action(AI.Action.LEAVE)

            prevX, prevY = self.prevMove

            if number >= 0:
                # This avoids setting -1 for bombs
                self.board[prevX][prevY] = number

            self.update_effective_label_board()

            self.mark_zero_squares(number)
            self.mark_guaranteed_squares()

            # # TODO: Remove before submission
            # if datetime.now() > self.start_time + timedelta(0, 5 * 60):
            #     raise self.CutoffTimeReached()

            flag_action = self.get_flag_action()
            if flag_action:
                return flag_action

            # Generate more moves if the above 100% algorithms can't find any
            if len(self.moves) == 0:
                # self.tank_algorithm()
                self.depth_search()

            if len(self.moves) == 0 and len(self.bombs) != self.totalMines:
                # We have to guess
                covered = self.get_all_covered_squares().difference(self.bombs)
                self.moves.add(covered.pop())

            return self.get_next_move()
        except:
            # print("ERROR IN MAIN LOOP")
            traceback.print_exc()

            if len(self.moves) != 0:
                x, y = self.moves.pop()
                return Action(AI.Action.UNCOVER, x, y)
            else:
                covered_squares = self.get_all_covered_squares()
                covered_squares.difference_update(self.bombs)
                x, y = covered_squares.pop()
                return Action(AI.Action.UNCOVER, x, y)

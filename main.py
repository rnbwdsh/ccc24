import itertools
import os
import webbrowser
from typing import Tuple, List

import matplotlib.pyplot as plt
import numpy as np

from submitter import submit, URL_PLAY

dir2complex = {"W": -1, "D": 1j, "S": 1, "A": -1j}
complex2dir = {v: k for k, v in dir2complex.items()}


def lvl1(line):
    w, d, s, a = [line.count(i) for i in "WDSA"]
    return f"{w} {d} {s} {a}"


def lvl2(line, start: complex = None, field: np.ndarray = None):
    pos = start or 0
    seen = {pos: 0}
    for idx, c in enumerate(line, 1):
        pos += dir2complex[c]
        if pos in seen and field is not None:
            print("self crash")
            return False
        seen[pos] = idx
        if start is not None and field is not None:
            try:
                xpos, ypos = int(pos.real), int(pos.imag)
                if field[xpos, ypos]:
                    print("tree crash")
                    return False
            except IndexError:
                print("out of field")
                return False
    # calculate min and max x
    min_x = min(p.real for p in seen)
    max_x = max(p.real for p in seen)
    # calculate min and max y
    min_y = min(p.imag for p in seen)
    max_y = max(p.imag for p in seen)
    # calculate area
    height = int(max_x - min_x + 1)
    width = int(max_y - min_y + 1)
    if start is None:
        return width, height, int(-min_x), int(-min_y)
    else:
        # visited all cells without a tree, did not leave the lawn
        all_visited = len(seen) + field.sum() == field.size
        print("all visited", all_visited)
        return all_visited


def lvl3(lines):
    res = []
    while lines:
        xdim, ydim = map(int, lines.pop(0).split())
        field = np.zeros((ydim, xdim), dtype=bool)
        for y, line in enumerate(lines[:ydim]):
            field[y] = [c == "X" for c in line]
        lines = lines[ydim:]
        path = lines.pop(0)
        res.append(lvl3_inner(path, field))
    return "\n".join(map(lambda b: "VALID" if b else "INVALID", res)) + "\n"


def lvl3_inner(path: str, field: np.ndarray) -> bool:
    """ check if field is valid, so if it doesn't self cross and doesn't collide with a tree"""
    width, height, xpos, ypos = lvl2(path)
    if not (width <= field.shape[1] and height <= field.shape[0]):
        print("driving out of field")
        return False
    start = xpos + ypos * 1j
    return lvl2(path, start=start, field=field)


def lvl4(lines: List[str]):
    """ first line contains x/y, then the field with exactly 1 tree """
    out = []
    while lines:
        xdim, ydim = map(int, lines.pop(0).split())
        field = np.zeros((ydim, xdim), dtype=bool)
        for i, line in enumerate(lines[:ydim]):
            field[i] = [c == "X" for c in line]
        # find the tree
        tree = tuple(np.argwhere(field)[0])
        # print("tree", tree)
        lines = lines[ydim:]
        out.append(lvl4_inner(field.shape, tree))
    return "\n".join(out) + "\n"


def lvl4_inner(shape, tree):
    """ generate a pathgen.py that visits all cells without a tree """
    directions_any_order = list(map(list, itertools.permutations(complex2dir, 4)))
    for x, y, policy in itertools.product(range(shape[0]), range(shape[1]), directions_any_order):
        path_steps = generate(*shape, tree, start=(x, y), policy=policy)
        if path_steps is not None:
            return path_steps
    else:
        print(shape, tree)
        raise RuntimeError


def generate(x_dim: int, y_dim: int, tree: tuple, start: Tuple[int, int], policy: List[complex], draw_path=True):
    if start == tree:
        return None
    pos = complex(*start)
    seen = {pos, complex(*tree)}
    path = [start]
    steps = ""
    for _ in range(x_dim * y_dim - 2):
        for next_move in policy:
            pos_next = pos + next_move
            if pos_next not in seen and (0 <= pos_next.real < x_dim) and (0 <= pos_next.imag < y_dim):
                pos = pos_next
                steps += complex2dir[next_move]
                path.append((pos_next.real, pos_next.imag))
                seen.add(pos)
                break
        else:
            return None
    if draw_path:
        f = plt.figure(figsize=(x_dim+1, y_dim+1), dpi=72)
        plt.plot(*zip(*path))
        # plt.show()
        plt.grid(True)
        # draw a big X for the tree
        plt.scatter(*tree, s=200, c="red", marker="x")
        plt.axis("equal")
        plt.savefig(f"data/img/{x_dim}_{y_dim}_{tree}.png")
        plt.close(f)
    return steps


if __name__ == "__main__":
    level = 4
    done = set(open("data/done.txt").read().strip().split("\n"))
    todo_this_level = len([f for f in os.listdir("data") if f.startswith(f"level{level}_") and f.endswith(".in")])
    for i in ["example"] + list(range(1, todo_this_level + 1)):
        example = f"level{level}_{i}"
        f_in = f"data/{example}.in"
        # check if the example.in exists and is not done
        if not os.path.exists(f_in):
            continue
        lines = open(f_in).read().strip().split("\n")[1:]
        lvl_func = globals()[f"lvl{level}"]
        if level < 2:
            res = "\n".join([lvl_func(line) for line in lines]) + "\n"
        else:
            res = lvl_func(lines)
        if i == "example" or example in done:
            expected = open(f"data/{example}.out").read()
            # assert res == expected, f"{res}\n\n{expected}"
            print(i)
        else:
            open(f"data/level{level}_{i}.out", "w").write(res)
            submit(example)

    # check if all examples are done
    done_this_level = len([f for f in os.listdir("data") if f.startswith(f"level{level}_") and f.endswith(".out")])
    if done_this_level == todo_this_level:
        # increase level
        fc = open(__file__, "r").read()
        # open(__file__, "w").write(fc.replace(f"level = {level}", f"level = {level + 1}"))
        # webbrowser.open(URL_PLAY)

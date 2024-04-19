import os
from random import shuffle

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import networkx as nx
import webbrowser
from submitter import submit, URL_PLAY


# Rock, Paper, Scisscors, Lizard, Spock=Y
KILL_LOOKUP = {
    frozenset("RS"): "R",
    frozenset("PR"): "P",
    frozenset("PS"): "S",
    # extend by Y = spock, and L = lizard
    frozenset("RL"): "R",
    frozenset("LP"): "L",
    frozenset("PS"): "S",
    frozenset("SR"): "R",
    frozenset("RP"): "P",
    frozenset("SP"): "S",
    frozenset("YR"): "R",
    frozenset("YL"): "L",
    frozenset("YP"): "Y",
    frozenset("YS"): "S",
    frozenset("LS"): "L",
    frozenset("LR"): "L",
}


def fight(line):
    sl = frozenset(line)
    if len(sl) == 1:
        return line[0]
    return KILL_LOOKUP[sl]


def lvl1(fn):
    lines = open(fn).read().strip().split("\n")[1:]
    out = [fight(line) for line in lines]
    return "\n".join(out) + "\n"


def fight2(line):
    # split into chunks of 2, reduce to 2
    for _ in range(2):
        line = [fight(line[i:i+2]) for i in range(0, len(line), 2)]
    return "".join(line)


def lvl2(fn):
    lines = open(fn).read().strip().split("\n")[1:]
    out = [fight2(line) for line in lines]
    return "\n".join(out) + "\n"


def generate_fighters1(line):
    """ a line is like 4R 3P 1S
    we want to generate it so that no rock fighters and at least one scissor fighter is left """
    line = line.split(" ")
    r = int(line[0][:-1])
    p = int(line[1][:-1])
    s = int(line[2][:-1])
    oout = "R" * r + "P" * p + "S" * s
    out = ""
    while r > 1:
        rc = min(3, r)
        pc = 4 - rc
        sc = 0
        if pc > p:
            pc = p
            sc = 4 - rc - pc
            s -= sc
        out += "S" * sc + "R" * rc + "P" * pc
        r -= rc
        p -= pc
    out += "R" * r + "P" * p + "S" * s
    fight_result = fight2(out)
    print(out, fight_result, line)
    assert "R" not in fight_result
    assert "S" in fight_result
    assert len(out) == len(oout)
    return out


def lvl3(fn):
    lines = open(fn).read().strip().split("\n")[1:]
    out = [generate_fighters1(line) for line in lines]
    return "\n".join(out) + "\n"


def fight3(line):
    # split into chunks of 2, reduce to 2
    while len(line) > 1:
        line = [fight(line[i:i+2]) for i in range(0, len(line), 2)]
        # print(line)
    return "".join(line)


def generate_fighters2(line):
    """ a line is like 4R 3P 1S
    we want to generate it so that no rock fighters and at least one scissor fighter is left """
    line = line.split(" ")
    r = int(line[0][:-1])
    p = int(line[1][:-1])
    s = int(line[2][:-1])
    out = ""
    oout = "R" * r + "P" * p + "S" * s
    while (r+p+s) > 1:
        r, p, s, outp = generate_left2(r, p, s)
        out += outp
    out += "S"
    fight_result = fight3(out)
    print(out, fight_result, line)
    assert "S" in fight_result
    assert len(out) == len(oout), [len(out), len(oout)]
    return out


def generate_left2(r, p, s):
    oout = "R" * r + "P" * p + "S" * s
    out = ""
    finale_size = len(oout) // 2

    rc = min(finale_size-1, r)
    pc = finale_size - rc
    sc = 0
    if pc > p:
        pc = p
        sc = finale_size - rc - pc
        s -= sc
    out += "P" * pc + "R" * rc + "S" * sc
    r -= rc
    p -= pc

    return r, p, s, out


def generate_fighters3(line, idx):
    """ a line is like 6R 5P 2S 3Y 0L
    generate pairings so that the winner is a scissors fighter """
    print("idx", idx)
    line = line.split(" ")
    r = int(line[0][:-1])
    p = int(line[1][:-1])
    s = int(line[2][:-1])
    y = int(line[3][:-1])
    l = int(line[4][:-1])
    out = list("S" * s + "L" * l + "P" * p + "Y" * y + "R" * r)
    fight_result = ""
    while fight_result != "S":
        shuffle(out)
        fight_result = fight3(out)
    return "".join(out)


def lvl4(fn):
    lines = open(fn).read().strip().split("\n")[1:]
    out = [generate_fighters3(line) for line in lines]
    return "\n".join(out) + "\n"


def lvl5(fn):
    print("file", fn)
    lines = open(fn).read().strip().split("\n")[1:]
    out = [generate_fighters3(line, idx) for idx, line in enumerate(lines)]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    level = 5
    done = set(open("data/done.txt").read().strip().split("\n"))
    todo_this_level = len([f for f in os.listdir("data") if f.startswith(f"level{level}_") and f.endswith(".in")])
    for i in ["example"] + list(range(1, todo_this_level + 1)):
        example = f"level{level}_{i}"
        # check if the example.in exists and is not done
        if not os.path.exists(f"data/{example}.in") or example in done:
            continue
        lvl_func = globals()[f"lvl{level}"]
        res = lvl_func(f"data/{example}.in")
        if i == "example":
            expected = open(f"data/{example}.out").read()
            # assert res == expected, f"{res}\n\n{expected}"
        else:
            open(f"data/level{level}_{i}.out", "w").write(res)
            submit(example)

    # check if all examples are done
    done_this_level = len([f for f in os.listdir("data") if f.startswith(f"level{level}_") and f.endswith(".out")])
    if done_this_level == todo_this_level:
        # increase level
        fc = open(__file__, "r").read()
        open(__file__, "w").write(fc.replace(f"level = {level}", f"level = {level + 1}"))
        webbrowser.open(URL_PLAY)
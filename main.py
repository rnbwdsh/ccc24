import itertools
import multiprocessing
import os
import webbrowser
from collections import Counter
from functools import cache
from random import choice
from typing import List, Optional, Dict, Tuple

import z3
from frozendict import frozendict
from z3 import Datatype, If, Or, Solver, Const, sat, And, Not

from submitter import submit, URL_PLAY


@cache
def fight(a, b):
    """ return the winner of a rock paper lizard spock game, where spock is Y """
    if a == b:
        return a
    if a == "R" and b in "LS":
        return a
    if a == "P" and b in "YR":
        return a
    if a == "S" and b in "PL":
        return a
    if a == "Y" and b in "RS":
        return a
    if a == "L" and b in "YP":
        return a
    return b


# create a Dict[str, set] to check which letter can be expanded to which other letters
expandable_lookup_map = {k: {v for v in "RPSYL" if fight(k, v) == k} for k in "RPSYL"}


def lvl1(line):
    return fight(*line)


def lvl2(line, to_end=False):
    # run 2 rounds of fights for an arbitrary number of players
    if to_end:
        while len(line) > 1:
            line = "".join([fight(line[i], line[i + 1]) for i in range(0, len(line), 2)])
        return line
    for _ in range(2):
        line = "".join([fight(line[i], line[i + 1]) for i in range(0, len(line), 2)])
    return line


def lvl3(line):
    """ line is a counter dict, i.e. 4R 3P 1S, always in that order, make it a Counter """
    budget = Counter({k: int("".join(v)) for *v, k in line.split(" ")})
    out = ""
    while sum(budget.values()) > 0:
        rc = min(budget["R"], 3)
        pc = min(budget["P"], 4-rc)
        sc = 4 - rc - pc
        chunk_out = "R" * rc + "P" * pc + "S" * sc
        if chunk_out == "RRPS":
            chunk_out = "RSRP"
        winner = lvl2(chunk_out)
        assert "R" not in winner, (winner, chunk_out)
        out += chunk_out
        budget -= Counter({"R": rc, "P": pc, "S": sc})
    winners = lvl2(out)
    assert "R" not in winners and "S" in winners, (winners, out)
    return out


@cache
def allowed_letters(budget: frozendict) -> frozenset:
    return frozenset([k for k, v in budget.items() if v > 0])


@cache
def generate_policy(allowed_targets: frozenset, allowed_sources: frozenset) -> Counter[frozendict]:
    last = [frozendict()]
    for key_pos, key in enumerate(allowed_sources, 1):
        allowed_possible_keys = allowed_targets & expandable_lookup_map[key]
        curr = [frozendict({**item, key: perm})
                for item in last
                for perm in itertools.permutations(allowed_possible_keys & expandable_lookup_map[key])]
        last = curr
    return curr


@cache
def expand_state_policy(budget: dict, to_expand: str, policy_a: frozendict, policy_b: Optional[frozendict], tresh: int, layer: int) -> Optional[str]:
    expanded = []
    budget = Counter(budget)
    policy = policy_a
    for exp_idx, curr in enumerate(to_expand):
        if exp_idx == tresh:
            policy = policy_b
        for try_expand in policy[curr]:
            if budget[try_expand] > 0:
                expanded.append(try_expand)
                expanded.append(curr)
                budget[try_expand] -= 1
                break
        else:
            return None
    if sum(budget.values()) == 0:
        return "".join(expanded)
    expand_func = expand_state_simple if policy_b is None else expand_state
    res = expand_func(frozendict(budget), "".join(expanded), layer + 1)
    if res is not None:
        return res


def my_cache(func):
    """ like the functools cache, but the to_expand parameter at pos 1 is sorted() before caching """
    cache = {}

    def wrapper(*args):
        key = (args[0], "".join(sorted(args[1])), *args[2:])
        if key not in cache:
            cache[key] = func(*args)
        return cache[key]

    return wrapper



@my_cache
def expand_state(budget: dict, to_expand: str, layer=0) -> Optional[str]:
    gpc = generate_policy(allowed_letters(budget), frozenset(to_expand))
    # sort keys by the number of times they appear in the Counter(policy)
    # print(f"{' ' * (layer)}{to_expand} {budget} {gpc}")
    for policy_a in gpc:
        for policy_b in gpc:
            for switch_idx in range(1, len(to_expand)) if policy_a != policy_b else [0]:
                res = expand_state_policy(frozendict(budget), to_expand, policy_a, policy_b, switch_idx, layer)
                if res is not None:
                    return res


@my_cache
def expand_state_simple(budget: dict, to_expand: str, layer=0) -> Optional[str]:
    gpc = generate_policy(allowed_letters(budget), frozenset(to_expand))
    # sort keys by the number of times they appear in the Counter(policy)
    # print(f"{' ' * (layer)}{to_expand} {budget} {gpc}")
    for policy in gpc:
        res = expand_state_policy(frozendict(budget), to_expand, policy, None, -1, layer)
        if res is not None:
            return res


def lvl4(line):
    budget = Counter({k: int("".join(v)) for *v, k in line.split(" ")})
    budget["S"] -= 1
    res = expand_state_simple(frozendict(budget), "S")
    if res is None:
        res = expand_state(frozendict(budget), "S")
        print("done with hard mode")
    if res is None:
        raise ValueError(f"No solution found for {line}/{budget}")
    print(line)
    assert lvl2(res, to_end=True) == "S", (res, line)
    return res


def lvl5(line):
    res = lvl4(line)
    return res



# Define the fighter symbols using Z3 Datatype
Fighter = Datatype('Fighter')
for name in "RPSYL":
    Fighter.declare(name)
Fighter = Fighter.create()


# Create a Z3 function to decide the winner based on the rules
def winner(a, b):
    return If(a == b, a,  # If the same, it's a tie
              If(Or(
                  And(a == Fighter.R, Or(b == Fighter.S, b == Fighter.L)),  # Rock wins
                  And(a == Fighter.P, Or(b == Fighter.R, b == Fighter.Y)),  # Paper wins
                  And(a == Fighter.S, Or(b == Fighter.P, b == Fighter.L)),  # Scissors wins
                  And(a == Fighter.Y, Or(b == Fighter.R, b == Fighter.S)),  # Spock wins
                  And(a == Fighter.L, Or(b == Fighter.P, b == Fighter.Y))),  # Lizard wins
                  a, b))


def replace_z(line: str, opts: str, cnt: int):
    for z_fill in opts:
        line2 = line.replace("Z", z_fill)
        yield line2
    for _ in range(cnt):
        line2 = line
        while "Z" in line2:
            # replace with random from opts
            line2 = line2.replace("Z", choice(opts), 1)
        yield line2


def generate_example(line: str, x_variables) -> Tuple[z3.Bool, Dict[int, z3.Const]]:
    fighters = []
    z_variables = {pos: Const("z"+str(pos), Fighter) for pos in range(len(line)) if line[pos] == "Z"}
    for i, symbol in enumerate(line):
        if symbol == "X":
            f = x_variables[i]
        elif symbol == "Z":
            f = z_variables[i]
        else:
            f = getattr(Fighter, symbol)
        fighters.append(f)
    while len(fighters) > 1:
        fighters = [winner(a, b) for a, b in zip(fighters[::2], fighters[1::2])]
    return fighters[0] == Fighter.S, z_variables


def template_in(m: z3.Model, res: List, x_variables: Dict[int, z3.Const], fill="X") -> str:
    for pos, x_var in x_variables.items():
        val = str(m[x_var])
        res[pos] = val if val != "None" else fill
    return "".join(res)


def lvl6(line, lvl7=False, cnt=1):
    # print(line)
    s = Solver()
    x_variables = {pos: Const(str(pos), Fighter) for pos in range(len(line)) if line[pos] == "X"}
    for line2 in replace_z(line, "RPSYL", cnt):
        clause, _ = generate_example(line2, x_variables)
        s.add(clause)

    while True:
        if s.check() != sat:
            raise ValueError(f"No solution found for {line}")

        res = template_in(s.model(), list(line), x_variables)
        # try to find any assignment of Z-variables where the winner is not  S
        clause, z_variables = generate_example(res, x_variables)
        s_ctr = Solver()
        s_ctr.add(Not(clause))
        if s_ctr.check() == sat:
            counter_line = template_in(s_ctr.model(), list(line), z_variables, fill="R")
            # counter_line_with_x = template_in(s.model(), list(counter_line), x_variables)
            # print(f"ctr-x {counter_line_with_x}")
            # win = lvl2(counter_line_with_x, to_end=True)
            # assert win != "S", (counter_line, win)
            # print(line, counter_line, counter_line_with_x, sep="\n")
            counter_example, _ = generate_example(counter_line, x_variables)
            s.add(counter_example)
        else:
            break

    # heuristic winner check
    for r in replace_z(res, "RPSYL", cnt=cnt*128):
        win = lvl2(r, to_end=True)
        if win != "S":
            print(f"retrying {line[:10]} with {cnt*4}")
            return lvl6(line, lvl7=lvl7, cnt=cnt*4)
    print(line, "".join(res), win)
    return "".join(res)


def lvl7(line):
    return lvl6(line, lvl7=True)


if __name__ == "__main__":
    level = 8
    done = set(open("data/done.txt").read().strip().split("\n"))
    todo_this_level = len([f for f in os.listdir("data") if f.startswith(f"level{level}_") and f.endswith(".in")])
    for i in ["example"] + list(range(1, todo_this_level + 1)):
        example = f"level{level}_{i}"
        f_in = f"data/{example}.in"
        # check if the example.in exists and is not done
        if not os.path.exists(f_in) or example in done:
            continue
        lines = open(f_in).read().strip().split("\n")[1:]
        lvl_func = globals()[f"lvl{level}"]
        with multiprocessing.Pool(16) as pool:
            res = "\n".join(pool.map(lvl_func, lines)) + "\n"
        # res = "\n".join([lvl_func(l) for l in lines]) + "\n"
        if i == "example" or example in done:
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

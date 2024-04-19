import os
import webbrowser
from collections import Counter

from submitter import submit, URL_PLAY


def fight(a, b):
    """ return the winner of a rock paper lizard spock game, where spock is Y """
    winning_chars = {"R": "LS", "P": "R", "S": "P", "L": "PS", "Y": "RL"}
    if a == b or (a in winning_chars and b in winning_chars[a]):
        return a
    return b


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


def lvl4(line):
    # expand so that you consume R first, then P, then S
    budget = Counter({k: int("".join(v)) for *v, k in line.split(" ")})
    budget["S"] -= 1
    out = "S"
    expansion_dicts = [
        {"R": "RS", "P": "RP", "S": "PS"},
        {"R": "SR", "P": "RP", "S": "PS"},
        {"R": "RS", "P": "PR", "S": "PS"},
        {"R": "SR", "P": "RP", "S": "PS"},
        {"R": "RS", "P": "RP", "S": "SP"},
        {"R": "SR", "P": "RP", "S": "SP"},
        {"R": "RS", "P": "PR", "S": "SP"},
        {"R": "SR", "P": "RP", "S": "SP"},
    ]

    def expand(iin, budget, expand_dict):
        nout = ""
        for i in iin:
            for try_expand in expand_dict[i]:
                if budget[try_expand] > 0:
                    nout += try_expand + i
                    budget[try_expand] -= 1
                    break
            else:
                raise ValueError("no expansion possible")
        if sum(budget.values()) == 0:
            for expand_dict in expansion_dicts:
                try:
                    nout, budget = expand(nout, budget.copy(), expand_dict)
                    break
                except ValueError:
                    pass
        return nout, budget

    for expand_dict in expansion_dicts:
        try:
            out, budget = expand(out, budget, expand_dict)
            break
        except ValueError:
            pass
    else:
        raise ValueError(":(")
    winner = lvl2(out, to_end=True)
    assert "S" == winner, (winner, out)
    return out


def lvl5(line):
    pass


if __name__ == "__main__":
    level = 1
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
        res = "\n".join([lvl_func(line) for line in lines]) + "\n"
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

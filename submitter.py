import requests

CHALLENGE_ID = 6575
SESSION = "ZmFhN2M3MWQtNTBjZC00N2VhLWFkZGUtNmQ1ZmZmYTYyNDI3"
XSRF = "be9e6a25-52e7-41db-a9b5-c0a2b309a40f"
URL_UPLOAD = f"https://catcoder.codingcontest.org/api/game/{CHALLENGE_ID}/upload/solution/"
URL_PLAY = f"https://catcoder.codingcontest.org/contest/{CHALLENGE_ID}"


def submit(challenge_id: str):
    # post to url with form data, i.e. body should look like this
    resp = requests.post(URL_UPLOAD + challenge_id,
                         cookies={"SESSION": SESSION, "XSRF-TOKEN": XSRF},
                         files={"file": (f"{challenge_id}.out", open(f"data/{challenge_id}.out"))})
    # assert resp.status_code == 200, challenge_id
    # assert resp.json()["results"][challenge_id] != "INVALID", challenge_id
    open("data/done.txt", "a").write(challenge_id + "\n")
    # print(challenge_id, resp.status_code, resp.text)

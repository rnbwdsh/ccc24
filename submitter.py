import requests

CHALLENGE_ID = 6142
SESSION = "YjE5ZmZiZjUtZTE3Yy00M2M1LWFjNjQtNTFjZmIyNWFiNDBl"
XSRF = "c112843d-374c-43fc-8062-7909e64a03ad"
URL_UPLOAD = f"https://catcoder.codingcontest.org/api/game/{CHALLENGE_ID}/upload/solution/"
URL_PLAY = f"https://catcoder.codingcontest.org/training/{CHALLENGE_ID}"


def asser(cond, msg):
    if not cond:
        print(msg)
    return cond


def submit(challenge_id: str):
    # post to url with form data, i.e. body should look like this
    """-----------------------------29968953953713868949546811206
    Content-Disposition: form-data; name="file"; filename="level1_1.out"
    Content-Type: application/octet-stream

    R
    R
    """
    resp = requests.post(URL_UPLOAD + challenge_id,
                         cookies={"SESSION": SESSION, "XSRF-TOKEN": XSRF},
                         files={"file": (f"{challenge_id}.out", open(f"data/{challenge_id}.out"))})
    done = asser(resp.status_code == 200, (challenge_id, resp.status_code, resp.text))
    done = asser(resp.json()["results"][challenge_id] != "INVALID", (challenge_id, resp.status_code, resp.text)) and done
    if done:
        open("data/done.txt", "a").write(challenge_id + "\n")
    # print(challenge_id, resp.status_code, resp.text)

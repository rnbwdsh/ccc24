import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service

CHALLENGE_ID = 6142
SESSION = "NDQ4OGJjYzUtZTIwMi00OTcyLWI2YjAtNzcwMjRlNjk0ZTRm"
XSRF = "84d9ec44-860d-4df2-8959-2a2be1f37115"
URL_UPLOAD = f"https://catcoder.codingcontest.org/api/game/{CHALLENGE_ID}/upload/solution/"
URL_PLAY = f"https://catcoder.codingcontest.org/training/{CHALLENGE_ID}"


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
    assert resp.status_code == 200, challenge_id
    assert resp.json()["results"][challenge_id] != "INVALID", challenge_id
    open("data/done.txt", "a").write(challenge_id + "\n")
    # print(challenge_id, resp.status_code, resp.text)

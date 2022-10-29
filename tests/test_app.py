import json

import requests

from src import RBuilder

RB = RBuilder.builder("http://127.0.0.1:8888/rentacar")
[
    RB.add_path(*x)
    for x in (
        ("CRUD", "crud"),  # base CRUD radical : rentacar/crud
        ("add", "add", "CRUD"),  # path add , extending CRUD path : rentacar/crud/add
        ("remove", "remove/<param>", "CRUD"),
        ("update", "update", "CRUD"),
        ("get", "get/<param>", "CRUD"),
        ("AUTH", "auth"),
        ("login", "login", "AUTH"),
        ("TEST", "test"),
    )
]


## test routes


def test_login_route():
    """Test the login route ."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
        "content-type": "application/x-www-form-urlencoded",
        "accept": "*/*",
    }
    r = requests.post(
        RB.path("login"),
        data={"user": "user", "password": "password"},
        headers=headers,
    )
    assert r.status_code == 200
    __json = json.loads(r.text)
    assert "token" in __json
    # user not recognizeed

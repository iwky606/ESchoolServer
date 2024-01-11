import json
from functools import wraps
from flask import g,redirect, url_for


def login_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if g.username:
            return func(*args, **kwargs)
        else:
            res={
                "msg":"请先登录!",
                "status":False
            }
            return json.dumps(res)

    return inner

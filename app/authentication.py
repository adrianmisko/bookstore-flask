from app import auth
from app.models import Client
from flask import g


@auth.verify_password
def verify_token(token, _):
    client = Client.verify_auth_token(token)
    if not client:
        return False
    g.client = client
    return True


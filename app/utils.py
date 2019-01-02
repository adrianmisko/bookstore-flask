from app import auth
from flask import g
from app.models import *
from decimal import Decimal


@auth.verify_password
def verify_password(username_or_token, password):
    client = Client.verify_auth_token(username_or_token)
    if not client:
        client = Client.query.filter_by(email=username_or_token).first()
        if not client or not client.verify_password(password):
            return False
    g.client = client
    return True


def calculate_price(item_id, quantity):
    return Book.query.filter_by(id=item_id).first().base_price * Decimal(quantity)


def get_single_image(obj):
    try:
        return obj.covers[0].path
    except IndexError:
        return None


def get_current_price(obj):
    return obj.base_price


def get_authors(obj):
    return [author.real_name for author in obj.get_authors()]

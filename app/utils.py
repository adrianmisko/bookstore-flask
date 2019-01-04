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


def get_authors(obj):
    return [author.real_name for author in obj.get_authors()]


def get_current_price(obj):
    for i in obj.product_pricings:
        if i.valid_from < datetime.datetime.now() < i.valid_until:
            return i.price
    return obj.base_price


def filter_by_author(name):
    author_name = AuthorName.query.filter_by(name=name).first()
    author = author_name.owner
    names = [an for an in author.names]
    books = []
    for an in names:
        books.extend(an.books)
    return books


def filter_by_genre(genre):
    gen = Genre.query.filter_by(name=genre).first()
    return gen.books


def filter_by_price(interval):
    price = interval.split(':')
    f = price[0]
    t = price[1]
    books = []
    for book in Book.query.all():
        current_price = get_current_price(book)
        if current_price>Decimal(f) and current_price<Decimal(t):
            books.append(book)
    return books


def filter_books(filter_by):
    books = []
    for key in filter_by.keys():
        if key == 'author':
            books.append(filter_by_author(filter_by[key]))
        if key == 'genre':
            books.append(filter_by_genre(filter_by[key]))
        if key == 'price':
            filter_by_price(filter_by[key])



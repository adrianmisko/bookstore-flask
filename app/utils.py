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


def get_current_price(id):
    book = Book.query.filter_by(id=id).first()
    for i in book.product_pricings:
        if datetime.datetime.now()<i.valid_until and datetime.datetime.now()>i.valid_from:
            return i.price
    return book.base_price


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


def filter_books(filter_by):
    books = []
    for key in filter_by.keys():
        if key == 'author':
            books.append(filter_by_author(filter_by[key]))
        if key == 'genre':
            books.append(filter_by_genre(filter_by[key]))
        if key == 'id':
            print(get_current_price(filter_by[key]))



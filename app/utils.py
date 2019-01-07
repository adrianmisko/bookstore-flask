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


def get_current_price(obj):
    pp = ProductPricing.query \
        .filter(
        and_(ProductPricing.book_id == obj.id,
             ProductPricing.valid_until > datetime.datetime.now(),
             ProductPricing.valid_from < datetime.datetime.now())) \
        .first()
    if pp is not None:
        return pp.price
    else:
        return obj.base_price


def get_single_image(obj):
    try:
        return obj.covers[0].path
    except IndexError:
        return None


def get_authors(obj):
    return [author.real_name for author in obj.get_authors()]


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
        current_price = book.get_current_price()
        if Decimal(f) < current_price < Decimal(t):
            books.append(book)
    return books


def filter_by_publisher(name):
    publisher = Publisher.query.filter_by(name=name).first()
    return publisher.books


def filter_by_tag(name):
    tag = Tag.query.filter_by(tag=name).first()
    return tag.books


def filter_books(filter_by):
    books = []
    # books = Book.query.filter(
    #      _and(
    #         Book.author.in_(make_list(filter_by[key])),
    #         ...
    #       )
    #   ).all()
    # FIND HOW TO INSPECT GENERATED QUERY
    for key in filter_by.keys():
        if key == 'author':
            books.append(set(filter_by_author(filter_by[key])))
        if key == 'genre':
            books.append(set(filter_by_genre(filter_by[key])))
        if key == 'price':
            books.append(set(filter_by_price(filter_by[key])))
        if key == 'publisher':
            books.append(set(filter_by_publisher(filter_by[key])))
        if key == 'tag':
            books.append(set(filter_by_tag(filter_by[key])))

    res = set.intersection(*books)
    return list(res)

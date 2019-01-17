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


def get_price_from_genres(obj):
    cd = CategoryDiscount.query.join(discounts_genres).join(Genre).join(books_genres) \
        .filter(
        and_(books_genres.c.book_id == obj.id,
             CategoryDiscount.valid_until >= datetime.datetime.now(),
             CategoryDiscount.valid_from <= datetime.datetime.now())) \
        .first()
    if cd is not None:
        return cd


def get_current_price(obj):
    cd = get_price_from_genres(obj)
    if cd is not None:
        if cd.discount_unit == 'PERCENTAGE':
            return obj.base_price * Decimal(0.01) * (Decimal(100) - cd.discount_value)
    else:
        pp = ProductPricing.query \
            .filter(
            and_(ProductPricing.book_id == obj.id,
                 ProductPricing.valid_until >= datetime.datetime.now(),
                 ProductPricing.valid_from <= datetime.datetime.now())) \
            .first()
        if pp is not None:
            return pp.price
        else:
            return Decimal(obj.base_price)


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

    options = ['authors_names', 'publishers', 'prices', 'genres', 'tags']
    query_args = {option: [] for option in options}

    for key in filter_by.keys():
        query_args[key + 's' if key + 's' in options else key] = filter_by.getlist(key)

    queries = {
        'authors_names': lambda authors: Book.id.in_(
            db.session.query(Book.id).join(authorships).join(AuthorName).join(Author).filter(
            Author.real_name.in_(authors))),
        'publishers': lambda publishers: Book.id.in_(
            db.session.query(Book.id).join(publishers_books).join(Publisher).filter(
                Publisher.name.in_(publishers))),
        'prices': lambda prices: Book.id.in_([row[0] for row in db.session.execute(
            'SELECT get_books_in_price_range(:f, :t)',
        {'f': Decimal(query_args['prices'][0].split(':')[0]),
         't': Decimal(query_args['prices'][0].split(':')[1])}).fetchall()]),
        'tags': lambda tags: Book.id.in_(
            db.session.query(Book.id).join(taggings).join(Tag).filter(
            Tag.tag.in_(tags))),
        'genres': lambda genres: Book.id.in_(
            db.session.query(Book.id).join(books_genres).join(Genre).filter(
            Genre.name.in_(genres))),

    }

    conditions = []
    for option in options:
        if query_args[option]:
            conditions.append(queries[option](query_args[option]))

    if filter_by.get('featured') == 'true':
        conditions.append(Book.id.in_(
        db.session.query(Book.id).filter(Book.is_featured == True)))
    if filter_by.get('available') == 'true':
        conditions.append(Book.id.in_(
            db.session.query(Book.id).filter(Book.number_in_stock > 0)))

    return Book.query.filter(*conditions).all()

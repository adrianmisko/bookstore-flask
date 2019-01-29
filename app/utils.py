from app import auth
from flask import g
from app.models import *
from decimal import Decimal, ROUND_HALF_UP


@auth.verify_password
def verify_password(username_or_token, password):
    client = Client.verify_auth_token(username_or_token)
    if not client:
        client = Client.query.filter_by(email=username_or_token).first()
        if not client or not client.verify_password(password):
            return False
    g.client = client
    return True


def calculate_price_both_present(base_price, discounts):
    pp_percent = discounts['product_pricing_discount_percent']
    pp_value = discounts['product_pricing_discount_value']
    cd_percent = discounts['category_discount_discount_percent']
    cd_value = discounts['category_discount_discount_value']

    after_pp_value = base_price - pp_value
    after_pp_percent = after_pp_value - (after_pp_value * Decimal(Decimal(pp_percent) / Decimal(100)))
    after_cd_value = after_pp_percent - cd_value
    after_cd_percent = after_cd_value - (after_cd_value * Decimal(Decimal(cd_percent) / Decimal(100)))

    return after_cd_percent.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


def calculate_price_category_discount_present(base_price, discounts):
    cd_percent = discounts['category_discount_discount_percent']
    cd_value = discounts['category_discount_discount_value']

    after_cd_value = base_price - cd_value
    after_cd_percent = after_cd_value - (after_cd_value * Decimal(Decimal(cd_percent) / Decimal(100)))

    return after_cd_percent.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


def calculate_price_product_pricing_present(base_price, discounts):
    pp_percent = discounts['product_pricing_discount_percent']
    pp_value = discounts['product_pricing_discount_value']

    after_pp_value = base_price - pp_value
    after_pp_percent = after_pp_value - (after_pp_value * Decimal(Decimal(pp_percent) / Decimal(100)))

    return after_pp_percent.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


def get_current_price(obj):
    values = db.session.execute('SELECT * FROM get_pricing(:_book_id)', {'_book_id': obj.id}).first().items()
    current_discounts = {}
    for tup in values:
        current_discounts[tup[0]] = tup[1]
    base_price = obj.base_price
    calculated_price = Decimal(0)
    if not current_discounts['category_discount_valid_until'] and not current_discounts['product_pricing_valid_until']:
        return base_price
    elif current_discounts['category_discount_valid_until'] and current_discounts['product_pricing_valid_until']:
        calculated_price = calculate_price_both_present(base_price, current_discounts)
    elif current_discounts['category_discount_valid_until']:
        calculated_price = calculate_price_category_discount_present(base_price, current_discounts)
    elif current_discounts['product_pricing_valid_until']:
        calculated_price = calculate_price_product_pricing_present(base_price, current_discounts)

    return calculated_price


def get_current_pricing(obj):
    values = db.session.execute('SELECT * FROM get_pricing(:_book_id)', {'_book_id': obj.id}).first().items()
    current_discounts = {}
    for tup in values:
        current_discounts[tup[0]] = tup[1]
    base_price = obj.base_price
    calculated_price = Decimal(0)
    if not current_discounts['category_discount_valid_until'] and not current_discounts['product_pricing_valid_until']:
        calculated_price = base_price
    elif current_discounts['category_discount_valid_until'] and current_discounts['product_pricing_valid_until']:
        calculated_price = calculate_price_both_present(base_price, current_discounts)
    elif current_discounts['category_discount_valid_until']:
        calculated_price = calculate_price_category_discount_present(base_price, current_discounts)
    elif current_discounts['product_pricing_valid_until']:
        calculated_price = calculate_price_product_pricing_present(base_price, current_discounts)

    current_discounts['price'] = calculated_price
    current_discounts['base_price'] = base_price
    return current_discounts


def calculate_price(item_id, quantity):
    book = Book.query.get(item_id)
    return get_current_price(book) * Decimal(quantity)


def get_single_image(obj):
    try:
        return obj.covers[0].path
    except IndexError:
        return None


def get_authors(obj):
    return [author.real_name for author in obj.get_authors()]


def filter_books(filter_by, page):

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
        db.session.query(Book.id).filter(Book.is_featured)))
    if filter_by.get('available') == 'true':
        conditions.append(Book.id.in_(
            db.session.query(Book.id).filter(Book.number_in_stock > 0)))

    return Book.query.filter(*conditions).paginate(page, app.config['PER_PAGE'], False)

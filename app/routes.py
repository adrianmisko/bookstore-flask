from app.schemas import *
from flask import request, jsonify
from app.utils import *
from marshmallow import ValidationError


@app.route('/')
@app.route('/index')
def index():
    return 'Hello, World!'


@app.route('/api/books', methods=['GET'])
def get_books():
    search_by = request.args.get('search')
    if search_by is None:
        if not request.args:
            books = Book.query.all().paginate(1, app.config['PER_PAGE'], False)
            return jsonify({
                'total': books.total,
                'data': books_compact_schema.dump(books.items).data
            }), 200
        else:
            page = request.args.get('page', 1, type=int)
            res = filter_books(request.args, page)
            if request.args.get('detailed'):
                return jsonify({
                    'total': res.total,
                    'data': books_schema.dump(res.items).data
                }), 200
            return jsonify({
                'total': res.total,
                'data': books_compact_schema.dump(res.items).data
            }), 200
    else:
        page = request.args.get('page', 1, type=int)
        books, found_total = Book.search(search_by, page=page)
        return jsonify(books_compact_schema.dump(books.all()).data), 200


@app.route('/api/books/<int:id>', methods=['GET'])
def get_book_by_id(id):
    return book_schema.jsonify(Book.query.filter_by(id=id).first()), 200


@app.route('/api/books/<int:id>/reviews', methods=['GET'])
def get_reviews(id):
    page = request.args.get('page', 1, type=int)
    book = Book.query.filter_by(id=id).first()
    if book is None:
        return 404
    reviews = book.reviews.paginate(page, app.config['PER_PAGE'], False)
    return jsonify({
        'total': reviews.total,
        'data': reviews_schema.dump(reviews.items).data
    }), 200


@app.route('/api/books/<int:id>/reviews', methods=['POST'])
def add_review(id):
    try:
        book = Book.query.filter_by(id=id).first()
        if book is None:
            return 404
        review_validator.validate(request.json)
        review = Review(
            author=request.json.get('author'),
            body=request.json.get('body'),
            mark=request.json.get('mark'),
        )
        book.reviews.append(review)
        db.session.commit()
        return jsonify(review_schema.dump(review).data), 201
    except ValidationError as err:
        print(err.messages)
        return jsonify(err.messages), 400


@app.route('/api/users/<int:id>/orders', methods=['GET'])
def get_users_orders(id):
    client = Client.query.filter_by(id=id).first()
    if client is None:
        return 404
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(client=client)\
        .order_by(Order.order_date.desc()).paginate(page, app.config['PER_PAGE'], False)
    return jsonify({
        'total': orders.total,
        'orders': orders_compact_schema.dump(orders.items).data
    }), 200


@app.route('/api/users/<int:client_id>/orders/<int:order_id>', methods=['GET'])
def get_order(client_id, order_id):
    order = Order.query.get(order_id)
    if order is None:
        return jsonify({'error': 404}), 404
    return jsonify(order_schema.dump(order).data), 200


@app.route('/api/users/<int:id>/orders', methods=['POST'])
def make_order(id):
    try:
        order = Order()
        items = [ItemOrdered(order=order, book=Book.query.get(item.get('id')), quantity=item.get('quantity'),
                             price=calculate_price(item.get('id'), item.get('quantity')))
                 for item in items_ordered_validating_schema.load(request.json.get('items')).data]
        order.items_ordered = items
        delivery_method = DeliveryMethod.query.filter_by(name=request.json.get('delivery_method')).first()
        order.total_price = sum([item.price for item in items]) + delivery_method.cost
        order.location = location_schema.load(request.json.get('location')).data
        order.client = Client.query.filter_by(id=id).first()
        order.delivery_method = delivery_method
        order.payment_method = PaymentMethod.query.filter_by(name=request.json.get('payment_method')).first()
        order.status = 'IN_PREPARATION'
        db.session.add(order)
        db.session.commit()
        return jsonify({'id': order.id}), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'error'}), 400


@app.route('/api/token', methods=['POST'])
@auth.login_required
def get_auth_token():
    token = g.client.generate_auth_token()
    return jsonify({
        'token': token.decode('ascii'),
        'id': g.client.id,
        'email': g.client.email,
        'name': g.client.name,
        'surname': g.client.surname
    }), 200


@app.route('/api/register', methods=['POST'])
def register():
    try:
        registration_client_schema.validate(request.json)
        client = client_schema.load(request.json).data
        db.session.add(client)
        db.session.commit()
        return jsonify({
            'id': client.id,
            'email': client.email,
            'name': client.name,
            'surname': client.surname
        }), 201
    except ValidationError as err:
        return jsonify(err.messages), 400


@app.route('/api/emails/validate', methods=['POST'])
def check_if_email_is_valid():
    try:
        email_validator.validate(request.json)
        return jsonify({'valid e-mail': True}), 200
    except ValidationError as err:
        return jsonify(err.messages), 400


@app.route('/api/phone_number/validate', methods=['POST'])
def check_if_phone_number_is_valid():
    try:
        phone_number_validator.validate(request.json)
        return jsonify({'valid phone number': True}), 200
    except ValidationError as err:
        return jsonify(err.messages), 400


@app.route('/api/genres', methods=['GET'])
def get_genres():
    genre = request.args.get('genre', False)
    if genre:
        genres = Genre.query.filter(Genre.name.ilike(genre + '%')).all()
        return jsonify(genres_schema.dump(genres).data), 200
    else:
        genres = Genre.query.all()
        return jsonify(genres_schema.dump(genres).data), 200


@app.route('/api/publishers', methods=['GET'])
def get_publishers():
    publisher = request.args.get('publisher', False)
    if publisher:
        publishers = Publisher.query.filter(Publisher.name.ilike(publisher + '%')).all()
        return jsonify(publishers_schema.dump(publishers).data), 200
    else:
        publishers = Publisher.query.all()
        return jsonify(publishers_schema.dump(publishers).data), 200


@app.route('/api/tags', methods=['GET'])
def get_tags():
    tag = request.args.get('tag', False)
    if tag:
        tags = Tag.query.filter(Tag.tag.ilike(tag + '%')).all()
        return jsonify(tags_schema.dump(tags).data), 200
    else:
        tags = Tag.query.all()
        return jsonify(tags_schema.dump(tags).data), 200


@app.route('/api/authors_names', methods=['GET'])
def get_authors_names():
    name = request.args.get('authors_name', False)
    if name:
        pen_names = db.select([AuthorName.name]).where(AuthorName.name.ilike('%' + name + '%'))
        real_names = db.session.query(Author.real_name).filter(Author.real_name.ilike('%' + name + '%')).subquery()
        q = pen_names.union(real_names).alias('union d')
        res = db.engine.execute(q).fetchall()
        return jsonify([{'name': r[0]} for r in res]), 200
    else:
        return jsonify(authors_names_schema.dump(AuthorName.query.all()).data), 200


@app.route('/api/min_price', methods=['GET'])
def get_min_price():
    min_price = db.session.execute('SELECT get_min_price()').scalar()
    return jsonify({'min': min_price}), 200


@app.route('/api/max_price', methods=['GET'])
def get_max_price():
    max_price = db.session.execute('SELECT get_max_price()').scalar()
    return jsonify({'max': max_price}), 200


@app.route('/api/delivery_methods', methods=['GET'])
def get_delivery_methods():
    delivery_methods = DeliveryMethod.query.all()
    return jsonify(delivery_methods_schema.dump(delivery_methods).data), 200


@app.route('/api/payment_methods', methods=['GET'])
def get_payment_methods():
    payment_methods = PaymentMethod.query.all()
    return jsonify(payment_methods_schema.dump(payment_methods).data), 200


@app.route('/api/users/<int:id>/locations', methods=['GET'])
def get_users_last_order_location(id):
    page = request.args.get('page', 1, type=int)
    locations = Location.query.join(Order).join(Client)\
        .filter(Client.id == id, Order._location_fk == Location.id)\
        .order_by(Order.order_date.desc()).paginate(page, app.config['PER_PAGE'], False)
    if not locations:
        return 404
    return jsonify({
        'total': locations.total,
        'data': locations_schema.dump(locations.items).data
        }), 200


@app.route('/api/users/<int:id>', methods=['GET'])
def get_user_details(id):
    client = Client.query.get(id)
    client.locations = Location.query.join(Order).join(Client)\
        .filter(Client.id == id, Order._location_fk == Location.id).order_by(Order.order_date.desc()).limit(5)
    if client is None:
        return 404
    return jsonify(client_details_schema.dump(client).data), 200


@app.route('/api/discounts', methods=['GET'])
def get_all_discounts():
    page = request.args.get('page', 1, type=int)
    cd = CategoryDiscount.query.all().page(1, app.config['PER_PAGE'], False)
    if cd is None:
        return 404
    return jsonify(category_discount_schema.dump(cd).data), 200


@app.route('/api/reviews/<int:id>/upvote', methods=['POST'])
def upvote_review(id):
    connection = db.engine.raw_connection()
    try:
        cursor = connection.cursor()
        cursor.callproc("upvote_review", [id])
        cursor.close()
        connection.commit()
        return jsonify({'ok': 'ok'}), 200
    except:
        return jsonify({'error': 'error'}), 400
    finally:
        connection.close()


@app.route('/api/reviews/<int:id>/downvote', methods=['POST'])
def downvote_review(id):
    connection = db.engine.raw_connection()
    try:
        cursor = connection.cursor()
        cursor.callproc("downvote_review", [id])
        cursor.close()
        connection.commit()
        return jsonify({'ok': 'ok'}), 200
    except:
        return jsonify({'error': 'error'}), 400
    finally:
        connection.close()


@app.route('/api/reviews/<int:id>/cancel_upvote', methods=['POST'])
def cancel_upvote(id):
    review = Review.query.get(id)
    if not review:
        return jsonify({'error': 'not found'}), 404
    else:
        review.upvotes = review.upvotes - 1
        db.session.commit()
        return jsonify({'ok': 'ok'}), 200


@app.route('/api/reviews/<int:id>/cancel_downvote', methods=['POST'])
def cancel_downvote(id):
    review = Review.query.get(id)
    if not review:
        return jsonify({'error': 'not found'}), 404
    else:
        review.downvotes = review.downvotes - 1
        db.session.commit()
        return jsonify({'ok': 'ok'}), 200





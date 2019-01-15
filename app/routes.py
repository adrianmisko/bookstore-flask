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
            books = Book.query.all()
            return jsonify(books_compact_schema.dump(books).data), 200
        else:
            books = filter_books(request.args)
            if request.args.get('detailed'):
                return jsonify(books_schema.dump(books).data), 200
            return jsonify(books_compact_schema.dump(books).data), 200
    else:
        page = request.args.get('page') or 1
        books, found_total = Book.search(search_by, page=page)
        return jsonify(books_compact_schema.dump(books.all()).data), 200


@app.route('/api/books/<int:id>', methods=['GET'])
def get_book_by_id(id):
    return book_schema.jsonify(Book.query.filter_by(id=id).first()), 200


@app.route('/api/books/<int:id>/reviews', methods=['GET'])
def get_reviews(id):
    book = Book.query.filter_by(id=id).first()
    if book is None:
        return 404
    return jsonify(reviews_schema.dump(book.reviews).data), 200


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
    return jsonify(orders_compact_schema.dump(client.orders).data), 200


@app.route('/api/users/<int:client_id>/orders/<int:order_id>', methods=['GET'])
def get_order(client_id, order_id):
    order = Order.query.filter_by(id=order_id).first()
    if order is None:
        return 404
    return jsonify(order_schema.dump(order).data), 200


@app.route('/api/users/<int:id>/orders', methods=['POST'])
def make_order(id):
    try:
        order = Order()
        items = [ItemOrdered(order=order, book=Book.query.get(item.get('id')), quantity=item.get('quantity'),
                             price=calculate_price(item.get('id'), item.get('quantity')))
                 for item in items_ordered_schema.load(request.json.get('items')).data]
        order.delivery_method = DeliveryMethod.query.filter_by(name=request.json.get('delivery_method')).first()
        order.payment_method = PaymentMethod.query.filter_by(name=request.json.get('payment_method')).first()
        order.items_ordered = items
        order.total_price = sum([item.price for item in items]) + order.delivery_method.cost
        order.client = Client.query.filter_by(id=id).first()
        order.location = location_schema.load(request.json.get('location')).data
        db.session.add(order)
        db.session.commit()
        return jsonify({'id': order.id}), 201
    except ValidationError as err:
        return jsonify(err.messages), 400


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
        names = db.session.query(Author).filter(Author.real_name.ilike('%' + name + '%')).all()
        if names:
            return jsonify(authors_schema.dump(names).data), 200
        else:
            names = db.session.query(AuthorName).filter(AuthorName.name.ilike('%' + name + '%')).all()
            return jsonify(authors_names_schema.dump(names).data), 200
    else:
        authors_names = AuthorName.query.all()
        return jsonify(authors_names_schema.dump(authors_names).data), 200


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

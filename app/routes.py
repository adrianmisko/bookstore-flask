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
    return jsonify(books_schema.dump(Book.query.all()))


@app.route('/api/books/<int:id>', methods=['GET'])
def get_book_by_id(id):
    return book_schema.jsonify(Book.query.filter_by(id=id).first())


@app.route('/api/users/<int:id>/orders')
@auth.login_required
def get_users_orders(id):
    if g.client.id != id:
        return jsonify({'Error': 'You aren\'t permitted to see get this resource'}), 403
    return jsonify({'Status': '200 OK'}), 200


@app.route('/api/token', methods=['POST'])
@auth.login_required
def get_auth_token():
    token = g.client.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


@app.route('/api/register', methods=['POST'])
def try_add_client():
    try:
        registration_client_schema.validate(request.json)
        client = client_schema.load(request.json).data
        db.session.add(client)
        db.session.commit()
        return jsonify({'email': client.email}), 201
    except ValidationError as err:
        return jsonify(err.messages)

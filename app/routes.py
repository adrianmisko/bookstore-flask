from app.schemas import *
from flask import request, abort, jsonify
from app.utils import *
from marshmallow import ValidationError

@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"


@app.route('/api/books', methods=['GET'])
def get_books():
    return jsonify(books_schema.dump(Book.query.all()))


@app.route('/api/books/<id>', methods=['GET'])
def get_book_by_id(id):
    return book_schema.jsonify(Book.query.filter_by(id=id).first())


@app.route('/api/users/<id>/orders')
@auth.login_required
def get_users_orders(id):
    if g.client.id != int(id):
        return jsonify({"Error": "You aren't permitted to see get this resource"})
    return jsonify({"Status": "200 OK"})


@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.client.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


@app.route('/api/register', methods=['POST'])
def try_add_client():
    try:
        client = client_schema.load(request.json).data
        print(client)
        db.session.add(client)
        db.session.commit()
        return jsonify({'ok': 'ok'})
    except ValidationError as err:
        return jsonify(err.messages)

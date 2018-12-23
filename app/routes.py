from app.schemas import *
from flask import request, abort, jsonify
from app.utils import *


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
        return jsonify({"nie twoje": "nie twoje"})
    return jsonify({"ok": "ok"})


@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.client.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


@app.route('/api/users', methods=['POST'])
def new_user():
    email = request.json.get('email')
    password = request.json.get('password')
    phone_number = request.json.get('phone number')
    name = request.json.get('surname')
    surname = request.json.get('name')
    if email is None or password is None:
        abort(400)
    if Client.query.filter_by(email=email).first() is not None:
        abort(400)
    client = Client(name=name, surname=surname, phone_number=phone_number, email=email)
    client.hash_password(password)
    db.session.add(client)
    db.session.commit()
    return jsonify({'email': client.email}, 201)

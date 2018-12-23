from app import app, auth
from app.models import *
from app.schemas import *
from flask import request, abort, jsonify, url_for


@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"


@app.route('/api/books/<id>', methods=['GET'])
def get_book_by_id(id):
    book = Book.query.filter_by(id=id).first()
    result = book_schema.jsonify(book)
    return result


@auth.login_required
@app.route('api/users/<id>/orders')
def get_users_orders(id):
    print('orders' + id)


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

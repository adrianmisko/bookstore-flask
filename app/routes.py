from app import app
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


@app.route('/api/users', methods=['POST'])
def new_user():
    email = request.json.get('email')
    password = request.json.get('password')
    if email is None or password is None:
        abort(400)
    if Client.query.filter_by(email=email).first() is not None:
        abort(400)
    client = Client(name='placeholder', surname='placeholder', phone_number='1', email=email)
    client.hash_password(password)
    db.session.add(client)
    db.session.commit()
    return jsonify({'username': client.username}), 201, {'Location': url_for('get_user', id=client.id, _external=True)}

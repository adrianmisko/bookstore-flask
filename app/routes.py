from app import app
from app.models import *
from app.schemas import *

@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"


@app.route('/api/books/<id>', methods=['GET'])
def get_book_by_id(id):
    book = Book.query.filter_by(id=id).first()
    print(book)
    result = book_schema.jsonify(book)
    print(result)
    return result

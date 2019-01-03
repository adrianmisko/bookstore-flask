from app import db, app
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from app.search import add_to_index, remove_from_index, query_index
import datetime


class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page=1, per_page=10):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class Book(SearchableMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ISBN = db.Column(db.String(13), index=True, unique=True)
    title = db.Column(db.String(64), index=True, nullable=False)
    release_date = db.Column(db.Date)
    description = db.Column(db.String(2048))
    base_price = db.Column(db.Numeric(11, 2), nullable=False)
    number_in_stock = db.Column(db.Integer, nullable=False)
    is_featured = db.Column(db.Boolean, index=True, nullable=False)

    covers = db.relationship('Cover', backref='book', lazy='joined')
    product_pricings = db.relationship('ProductPricing', backref='book', lazy='dynamic')
    tags = db.relationship('Tag', secondary='taggings', backref='books', lazy='joined')
    reviews = db.relationship('Review', backref='book', lazy='dynamic')
    authors_names = db.relationship('AuthorName', secondary='authorships', backref='books', lazy='joined')
    genres = db.relationship('Genre', secondary='books_genres', backref='books', lazy='dynamic')
    publishers = db.relationship('Publisher', secondary='publishers_books', backref='books', lazy='dynamic')

    __searchable__ = ['title', 'genres', 'authors_names', 'publishers', 'authors', 'ISBN']

    @staticmethod
    def get_featured():
        return Book.query.filter(Book.is_featured).all()

    def get_authors(self):
        return [name.owner for name in self.authors_names]

    def __repr__(self):
        return '<Book \'{}\'>'.format(self.title)


class Cover(db.Model):
    path = db.Column(db.String(128), primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), index=True)

    def __repr__(self):
        return '<Cover \'{}\'>'.format(self.path)


class ProductPricing(db.Model):
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), primary_key=True)
    valid_until = db.Column(db.DateTime, primary_key=True)
    valid_from = db.Column(db.DateTime, nullable=False, index=True)
    price = db.Column(db.Numeric(11, 2), nullable=False)
    discount_unit = db.Column(db.String(32), nullable=False)
    min_order_value = db.Column(db.Numeric(11, 2), nullable=False)
    max_discount_amount = db.Column(db.Numeric(11, 2))

    def __repr__(self):
        return '<Product pricing book_id: {}, price: {}>'.format(self.book_id, self.price)


class Tag(db.Model):
    tag = db.Column(db.String(64), primary_key=True)

    def __repr__(self):
        return '<Tag \'{}\'>'.format(self.tag)


taggings = db.Table('taggings',
    db.Column('tag', db.String(64), db.ForeignKey('tag.tag', ondelete="CASCADE"), primary_key=True),
    db.Column('book_id', db.Integer, db.ForeignKey('book.id', ondelete="CASCADE"), primary_key=True)
)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    author = db.Column(db.String(128), nullable=False)
    body = db.Column(db.String(4096), nullable=False)
    mark = db.Column(db.Integer, nullable=False)
    upvotes = db.Column(db.Integer, nullable=False)
    downvotes = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Review book_id: {}, author: \'{}\'>'.format(self.book_id, self.author)


class AuthorName(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))

    def __repr__(self):
        return '<AuthorName \'{}\'>'.format(self.name)


authorships = db.Table('authorships',
    db.Column('id', db.Integer, db.ForeignKey('author_name.id'), primary_key=True),
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('author_order', db.Integer)
)


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    real_name = db.Column(db.String(128), nullable=False, index=True)

    names = db.relationship('AuthorName', backref='owner', lazy='dynamic')

    def __repr__(self):
        return '<Author \'{}\'>'.format(self.real_name)


class Genre(db.Model):
    name = db.Column(db.String(32), primary_key=True)

    discounts = db.relationship('CategoryDiscount', secondary='discounts_genres',
                                backref='genres', lazy='joined')

    def __repr__(self):
        return '<Genre \'{}\'>'.format(self.name)


books_genres = db.Table('books_genres',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('genre_name', db.String(32), db.ForeignKey('genre.name'), primary_key=True),
)


class CategoryDiscount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discount_value = db.Column(db.Numeric(11, 2))
    discount_percent = db.Column(db.Integer)
    valid_from = db.Column(db.DateTime, index=True)
    valid_until = db.Column(db.DateTime, index=True)
    min_order_value = db.Column(db.Numeric(11, 2))
    max_discount_amount = db.Column(db.Numeric(11, 2))

    def __repr__(self):
        return '<Discount for genres \'{}\' valid until \'{}\'>'.format(self.genres, self.valid_until)


discounts_genres = db.Table('discounts_genres',
    db.Column('category_discount_id', db.Integer,
                                     db.ForeignKey('category_discount.id'), primary_key=True),
    db.Column('genre_name', db.String(32), db.ForeignKey('genre.name'), primary_key=True)
)


class Publisher(db.Model):
    name = db.Column(db.String(128), primary_key=True)

    def __repr__(self):
        return '<Publisher \'{}\'>'.format(self.name)


publishers_books = db.Table('publishers_books',
    db.Column('publisher_name', db.String(128), db.ForeignKey('publisher.name'), primary_key=True),
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True)
)


class ItemOrdered(db.Model):
    order_id = db.Column(db.Integer,  db.ForeignKey('order.id'), primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric, nullable=False)

    book = db.relationship('Book', lazy='select')

    def __repr__(self):
        return '<ItemOrdered book: {} quantity: {} price: {}>'.format(self.book, self.quantity, self.price)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), index=True)
    _location_fk = db.Column(db.Integer, db.ForeignKey('location.id'), index=True)
    payment_method_name = db.Column(db.String(64), db.ForeignKey('payment_method.name'), index=True)
    delivery_method_name = db.Column(db.String(64), db.ForeignKey('delivery_method.name'), index=True)
    payment_id = db.Column(db.Integer, nullable=True, index=True)
    order_date = db.Column(db.DateTime, nullable=False, index=True, default=datetime.datetime.utcnow)
    payment_date = db.Column(db.DateTime, nullable=True, index=True)
    total_price = db.Column(db.Numeric, nullable=False)

    items_ordered = db.relationship('ItemOrdered', backref='order', lazy='joined')
    client = db.relationship('Client', backref='orders', lazy='joined')
    location = db.relationship('Location', backref='orders', lazy='joined')
    delivery_method = db.relationship('DeliveryMethod', lazy='joined')
    payment_method = db.relationship('PaymentMethod', lazy='joined')

    def __repr__(self):
        return '<Order {} on {}>'.format(self.id, self.order_date)


class PaymentMethod(db.Model):
    name = db.Column(db.String(64), primary_key=True)

    def __repr__(self):
        return '<PaymentMethod \'{}\'>'.format(self.name)


class DeliveryMethod(db.Model):
    name = db.Column(db.String(64), primary_key=True)

    def __repr__(self):
        return '<DeliveryMethod \'{}\'>'.format(self.name)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place = db.Column(db.String(64), nullable=False)
    street_name = db.Column(db.String(128), nullable=False)
    street_number = db.Column(db.String(8), nullable=False)
    zip_code = db.Column(db.String(64), nullable=False, index=True)

    __table_args__ = (db.Index('location_index', place, street_name, street_number), )

    def __repr__(self):
        return '<Location {} {} {} {}>'.format(self.zip_code, self.place, self.street_name, self.street_number)


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    surname = db.Column(db.String(128), index=True)
    phone_number = db.Column(db.String(32), nullable=False, unique=True, index=True)
    email = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)

    opinions = db.relationship('Opinion', backref='client', lazy='joined')

    def generate_auth_token(self, expiration=300):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        return Client.query.get(data['id'])

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256:10000')

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<Client \'{} {} {}\'>'.format(self.name, self.surname, self.email)


class Opinion(db.Model):
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), primary_key=True)
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(2048))
    mark = db.Column(db.Integer, nullable=False)
    upvotes = db.Column(db.Integer)
    downvotes = db.Column(db.Integer)

    def __repr__(self):
        return '<Opinion {} from {}>'.format(self.id, self.client)



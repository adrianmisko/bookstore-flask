from app import db


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), index=True, nullable=False)
    release_date = db.Column(db.Date)
    description = db.Column(db.String(2048))
    base_price = db.Column(db.Numeric(11,2), nullable=False)
    number_in_stock = db.Column(db.Integer, nullable=False)
    is_featured = db.Column(db.Boolean, index=True, nullable=False)

    cover = db.relationship('Cover', backref='book', lazy='dynamic')
    product_pricing = db.relationship('ProductPricing', backref='book', lazy='dynamic')
    tags = db.relationship('Tag', secondary='taggings', backref='books', lazy='joined')
    review = db.relationship('Review', backref='book', lazy='dynamic')
    authors_names = db.relationship('AuthorName', secondary='authorships', backref='books', lazy='joined')


    @staticmethod
    def get_featured():
        return Book.query.filter(Book.is_featured == True).all()

    def __repr__(self):
        return '<Book {}>'.format(self.title)


class Cover(db.Model):
    path = db.Column(db.String(128), primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), index=True)

    def __repr__(self):
        return '<Cover {}>'.format(self.path)


class ProductPricing(db.Model):
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), primary_key=True)
    valid_until = db.Column(db.DateTime, primary_key=True)
    valid_from = db.Column(db.DateTime, nullable=False, index=True)
    price = db.Column(db.Numeric(11, 2), nullable=False)
    discount_unit = db.Column(db.String(32), nullable=False)
    min_order_value = db.Column(db.Numeric(11, 2), nullable=False)
    max_discount_amount = db.Column(db.Numeric(11, 2))

    def __repr__(self):
        return '<Product pricing {}: {}>'.format(self.book_id, self.price)


class Tag(db.Model):
    tag = db.Column(db.String(64), primary_key=True)

    def __repr__(self):
        return '<Tag {}>'.format(self.tag)


taggings = db.Table('taggings',
    db.Column('tag', db.String(64), db.ForeignKey('tag.tag'), primary_key=True),
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True)
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
        return '<Review {}: {}>'.format(self.book_id, self.author)


class AuthorName(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))

    def __repr__(self):
        return '<AuthorName {}>'.format(self.name)


authorships = db.Table('authorships',
    db.Column('id', db.Integer, db.ForeignKey('AuthorName.id'), primary_key=True),
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('author_order', db.Integer)
)


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    real_name = db.Column(db.String(128), nullable=False, index=True)

    names = db.relationship('AuthorName', backref='owner', lazy='dynamic')

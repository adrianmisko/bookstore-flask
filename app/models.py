from app import db

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), index=True, nullable=False)
    release_date = db.Column(db.Date)
    description = db.Column(db.String(2048))
    base_price = db.Column(db.Float, nullable=False)
    number_in_stock = db.Column(db.Integer, nullable=False)
    is_featured = db.Column(db.Boolean, index=True, nullable=False)

    cover = db.relationship('Cover', backref='book', lazy='dynamic')

    def __repr__(self):
        return '<Book {}>'.format(self.title)


class Cover(db.Model):
    path = db.Column(db.String(128), primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), index=True)

    def __repr__(self):
        return 'Cover {}'.format(self.path)

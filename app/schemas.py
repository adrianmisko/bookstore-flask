from app.models import *
from app import ma
from marshmallow import post_load, validates, ValidationError
from flask import request

class AuthorNameSchema(ma.ModelSchema):
    class Meta:
        model = AuthorName
        fields = ('name',)


class BookSchema(ma.ModelSchema):
    class Meta:
        model = Book
    authors_names = ma.Nested(AuthorNameSchema, many=True)


class ClientSchema(ma.ModelSchema):
    class Meta:
        model = Client
        strict = True
        exclude = ('id', 'password_hash', 'opinions')

    @validates('email')
    def validate_email(self, email):
        if email is None or Client.query.filter_by(email=email).first() is not None:
            raise ValidationError('email wrong')

    @post_load
    def set_password_hash(self, client):
        password = request.json.get('password')
        if password is None:
            raise ValidationError('password bad')
        client.hash_password(password)
        return client


author_name_schema = AuthorNameSchema()
book_schema = BookSchema()
books_schema = BookSchema(many=True)
clinet_schema = ClientSchema()

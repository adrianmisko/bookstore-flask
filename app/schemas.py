from app import ma
from marshmallow import post_load, fields, validate
from flask import request
from app.validatros import *
from app.utils import *


class AuthorNameSchema(ma.ModelSchema):
    class Meta:
        model = AuthorName
        fields = ('name',)


class AuthorSchema(ma.ModelSchema):
    class Meta:
        model = Author
        fields = ('real_name',)


class PublisherSchema(ma.ModelSchema):
    class Meta:
        model = Publisher
        fields = ('name',)


class TagSchema(ma.ModelSchema):
    class Meta:
        model = Tag
        fields = ('tag',)


class GenreSchema(ma.ModelSchema):
    class Meta:
        model = Genre
        fields = ('name',)


class CoverSchema(ma.ModelSchema):
    class Meta:
        model = Cover
        fields = ('path',)


class BookCompactSchema(ma.ModelSchema):
    class Meta:
        model = Book
        fields = ('id', 'title', 'authors_names', 'tags', 'price', 'cover')

    authors_names = ma.Nested(AuthorNameSchema, many=True)
    tags = ma.Nested(TagSchema, many=True)
    price = fields.Function(get_current_price)
    cover = fields.Function(get_single_image)


class BookSchema(ma.ModelSchema):
    class Meta:
        model = Book
        fields = ('id', 'title', 'authors_names', 'publishers', 'genres', 'price', 'release_date',
                  'number_in_stock', 'is_featured', 'description', 'covers', 'tags', 'ISBN')

    authors_names = ma.Nested(AuthorNameSchema, many=True)
    publishers = ma.Nested(PublisherSchema, many=True)
    genres = ma.Nested(GenreSchema, many=True)
    covers = ma.Nested(CoverSchema, many=True)
    tags = ma.Nested(TagSchema, many=True)
    price = ma.Function(get_current_price)


class BookSearchableSchema(ma.ModelSchema):
    class Meta:
        model = Book
        fields = Book.__searchable__

    authors_names = ma.Nested(AuthorNameSchema, many=True)
    publishers = ma.Nested(PublisherSchema, many=True)
    genres = ma.Nested(GenreSchema, many=True)
    tags = ma.Nested(TagSchema, many=True)
    authors = ma.Function(get_authors, many=True)


class ReviewSchema(ma.ModelSchema):
    class Meta:
        model = Review
        strict = True


class ReviewValidator(ma.Schema):
    author = fields.String(validate=validate.Length(
                    min=1, max=128, error='Author field must be between 1 and 128 characters long'))
    body = fields.String(validate=validate.Length(
        min=15, max=4096, error='Author field must be between 15 and 4096 characters long'))
    mark = fields.Integer(validate=validate.Range(max=10, error='You can\'t rate more than 10 points (5 stars)'))


class ClientSchema(ma.ModelSchema):
    class Meta:
        model = Client
        strict = True
        exclude = ('id', 'password_hash', 'opinions')

    email = fields.Email(validate=validate_email, required=True)

    @post_load
    def set_password_hash(self, client):
        password = request.json.get('password')
        client.hash_password(password)
        return client


class RegistrationClientSchema(ClientSchema):
    class Meta:
        strict = True

    password = fields.String(required=True, validate=validate_password)


class EmailValidator(ma.Schema):
    class Meta:
        strict = True

    email = fields.Email(validate=validate_email, required=True)


class ItemsOrderedSchema(ma.Schema):
    class Meta:
        strict = True

    id = fields.Integer(required=True, validate=validate.Range(min=1, error='Invalid ID'))
    quantity = fields.Integer(required=True, validate=validate.Range(min=1, max=99,
                                                                     error='Quantity must be greater than 0 and less than 100'))


class PhoneNumberValidator(ma.Schema):
    class Meta:
        strict = True

    phone_number = fields.String(required=True, validate=validate_phone_number)


class LocationSchema(ma.Schema):
    class Meta:
        strict = True


book_schema = BookSchema()
books_schema = BookSchema(many=True)
books_compact_schema = BookCompactSchema(many=True)
client_schema = ClientSchema()
registration_client_schema = RegistrationClientSchema()
email_validator = EmailValidator()
book_searchable_schema = BookSearchableSchema()
items_ordered_schema = ItemsOrderedSchema(many=True)
phone_number_validator = PhoneNumberValidator()
reviews_schema = ReviewSchema(many=True)
review_schema = ReviewSchema()
review_validator = ReviewValidator()
genres_schema = GenreSchema(many=True)
tags_schema = TagSchema(many=True)
publishers_schema = PublisherSchema(many=True)
authors_names_schema = AuthorNameSchema(many=True)

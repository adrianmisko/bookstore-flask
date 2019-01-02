from app import ma
from marshmallow import post_load, fields, validate
from flask import request
from app.validatros import *


class AuthorNameSchema(ma.ModelSchema):
    class Meta:
        model = AuthorName
        fields = ('name', )


class AuthorSchema(ma.ModelSchema):
    class Meta:
        model = Author
        fields = ('real_name', )


class PublisherSchema(ma.ModelSchema):
    class Meta:
        model = Publisher
        fields = ('name', )


class TagSchema(ma.ModelSchema):
    class Meta:
        model = Tag
        fields = ('tag', )


class GenreSchema(ma.ModelSchema):
    class Meta:
        model = Genre
        fields = ('name', )


class CoverSchema(ma.ModelSchema):
    class Meta:
        model = Cover
        fields = ('path', )


class BookSchema(ma.ModelSchema):
    class Meta:
        model = Book
        fields = ('id', 'title', 'authors_names', 'tags', 'price', 'cover')
    authors_names = ma.Nested(AuthorNameSchema, many=True)
    tags = ma.Nested(TagSchema, many=True)
    price = fields.Method('get_current_price')
    cover = fields.Method('get_single_image')

    def get_single_image(self, obj):
        try:
            return obj.covers[0].path
        except IndexError:
            return None

    def get_current_price(self, obj):
        return obj.base_price


class BookDetailsSchema(ma.ModelSchema):
    class Meta:
        model = Book
        exclude = ()
    authors_names = ma.Nested(AuthorNameSchema, many=True)
    publishers = ma.Nested(PublisherSchema, many=True)
    genres = ma.Nested(GenreSchema, many=True)
    tags = ma.Nested(TagSchema, many=True)


class BookSearchableSchema(ma.ModelSchema):
    class Meta:
        model = Book
        fields = Book.__searchable__
    authors_names = ma.Nested(AuthorNameSchema, many=True)
    publishers = ma.Nested(PublisherSchema, many=True)
    genres = ma.Nested(GenreSchema, many=True)
    tags = ma.Nested(TagSchema, many=True)
    authors = ma.Method('get_authors', many=True)

    def get_authors(self, obj):
        return [author.real_name for author in obj.get_authors()]


class ClientSchema(ma.ModelSchema):
    class Meta:
        model = Client
        strict = True
        exclude = ('id', 'password_hash', 'opinions', 'name', 'surname')
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


book_schema = BookSchema()
books_schema = BookSchema(many=True)
client_schema = ClientSchema()
registration_client_schema = RegistrationClientSchema()
email_validator = EmailValidator()
book_searchable_schema = BookSearchableSchema()
items_ordered_schema = ItemsOrderedSchema(many=True)
phone_number_validator = PhoneNumberValidator()

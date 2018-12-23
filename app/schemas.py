from app.models import *
from app import ma


class AuthorNameSchema(ma.ModelSchema):
    class Meta:
        model = AuthorName
        exclude = ('id',)


class BookSchema(ma.ModelSchema):
    class Meta:
        model = Book
    authors_names = ma.Nested(AuthorNameSchema, many=True)


author_name_schema = AuthorNameSchema()
book_schema = BookSchema()

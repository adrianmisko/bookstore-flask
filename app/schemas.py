from app.models import *

class BookSchema(ma.ModelSchema):
    class Meta:
        model = Book
        exclude = ('id',)

book_schema = BookSchema()

class AuthorNameSchema(ma.ModelSchema):
    class Meta:
        model = AuthorName
        exclude = ('id',)

author_name_schema = AuthorNameSchema()
from app.models import *
from marshmallow import ValidationError


def validate_email(email):
    if email is None or email == '':
        raise ValidationError('E-mail field is required')
    elif Client.query.filter_by(email=email).first() is not None:
        raise ValidationError('This E-mail is already used')


def validate_password(password):
    rules = [lambda s: any(x.isupper() for x in s),
             lambda s: any(x.islower() for x in s),
             lambda s: any(x.isdigit() for x in s),
             lambda s: len(s) >= 8]
    if password is None or password == '':
        raise ValidationError('Password field is required')
    elif not all(rule(password) for rule in rules):
        raise ValidationError('Password needs to have at least 8 characters including one capital letter and one number')


def validate_phone_number(number):
    if number is None or number == '':
        raise ValidationError('Phone number field is required')
    elif not all(x.isdigit() for x in number):
        raise ValidationError('Phone number cannot include non-numeric characters')
    elif len(number) > 32:
        raise ValidationError('Phone number must have less than 32 numbers')
    elif Client.query.filter_by(phone_number=number).first() is not None:
        raise ValidationError('This number is already in use')

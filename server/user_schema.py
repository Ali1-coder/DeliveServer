from marshmallow import Schema, fields, validate, ValidationError

PASSWORD_REGEX = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*?&#]{6,}$'
PASSWORD_ERROR = "Password must contain at least one letter, one number, and be at least 6 characters long."


def validate_password_match(data):
    if data['password'] != data['confirm_password']:
        raise ValidationError("Passwords do not match.")


class UserRegisterSchema(Schema):
    first_name = fields.String(
        required=True,
        validate=validate.Length(
            min=1, 
            max=80,  # Matches model's String(80)
            error="First name must be between 1 and 80 characters."
        ),
        error_messages={"required": "First name is required."}
    )
    second_name = fields.String(
        required=True,
        validate=validate.Length(
            min=1, 
            max=80,  # Matches model's String(80)
            error="First name must be between 1 and 80 characters."
        ),
        error_messages={"required": "Second name is required."}
    )
    username = fields.String(
        required=True,
        validate=validate.Length(
            min=1, 
            max=80,  # Matches model's String(80)
            error="First name must be between 1 and 80 characters."
        ),
        error_messages={"required": "Username is required."}
    )
    email = fields.Email(
        required=True,
        validate=validate.Length(
            max=120,  # Matches model's String(120)
            error="Email must be less than 120 characters."
        ),
        error_messages={
            "required": "Email is required.",
            "invalid": "Invalid email address format."
        }
    )
    password = fields.String(
        required=True,
        validate=[
            validate.Length(min=6, error="Password must be at least 6 characters long."),
            validate.Regexp(PASSWORD_REGEX, error=PASSWORD_ERROR)
        ],
        error_messages={"required": "Password is required."}
    )
    confirm_password = fields.String(
        required=True,
        error_messages={"required": "Password confirmation is required."}
    )

    def validate(self, data, **kwargs):
        validate_password_match(data)
        return data



class UserLoginSchema(Schema):
    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required.",
            "invalid": "Invalid email format."
        }
    )
    password = fields.String(
        required=True,
        error_messages={"required": "Password is required."}
    )

class PasswordResetRequestSchema(Schema):
    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required.",
            "invalid": "Invalid email format."
        }
    )



class PasswordResetSchema(Schema):
    token = fields.Str(required=True)
    password = fields.String(
        required=True,
        validate=[
            validate.Length(min=6, error="Password must be at least 6 characters long."),
            validate.Regexp(PASSWORD_REGEX, error=PASSWORD_ERROR)
        ],
        error_messages={"required": "Password is required."}
    )
    confirm_password = fields.String(
        required=True,
        error_messages={"required": "Password confirmation is required."}
    )


    def validate(self, data, **kwargs):
        validate_password_match(data)
        return data



class UserBaseSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.String(dump_only=True)
    email = fields.Email(dump_only=True)
    is_admin = fields.Boolean(dump_only=True)

class UserUpdateSchema(Schema):
    username = fields.String(validate=validate.Length(min=1, max=80))
    email = fields.Email(validate=validate.Length(max=120))
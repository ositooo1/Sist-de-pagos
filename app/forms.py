from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import Usuario


class RegistroForm(FlaskForm):
    """Formulario de registro de usuario nuevo."""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(min=6)])
    confirmar = PasswordField(
        "Repetir contraseña",
        validators=[
            DataRequired(),
            EqualTo("password", message="Las contraseñas no coinciden"),
        ],
    )
    submit = SubmitField("Registrarme")

    def validate_email(self, field):
        """Evita emails duplicados."""
        if Usuario.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("Ese email ya está registrado.")


class LoginForm(FlaskForm):
    """Formulario de inicio de sesión."""

    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Ingresar")

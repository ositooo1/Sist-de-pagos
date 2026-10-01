from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField, TextAreaField,
                     DecimalField, IntegerField, SelectField)
from wtforms.validators import (DataRequired, Email, EqualTo, Length, ValidationError,
                                NumberRange, Optional, InputRequired)
from app.models import Usuario


class RegistroForm(FlaskForm):
    """Formulario de registro de usuario nuevo."""
    nombre = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(min=6)])
    confirmar = PasswordField("Repetir contraseña",
                              validators=[DataRequired(), EqualTo("password", message="Las contraseñas no coinciden")])
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


class ProductoForm(FlaskForm):
    """Formulario para crear y editar productos."""
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField("Descripción", validators=[Optional(), Length(max=500)])
    precio = DecimalField("Precio", places=2,
                          validators=[InputRequired(), NumberRange(min=0.01, message="El precio debe ser mayor a 0")])
    stock = IntegerField("Stock",
                         validators=[InputRequired(), NumberRange(min=0, message="El stock no puede ser negativo")])
    submit = SubmitField("Guardar")


class EliminarForm(FlaskForm):
    """Formulario vacío: solo aporta el token CSRF para borrar con POST."""
    submit = SubmitField("Eliminar")


class AccionForm(FlaskForm):
    """Formulario vacío: solo aporta el token CSRF para acciones por POST."""
    pass


class PagoForm(FlaskForm):
    """Formulario del simulador de pago."""
    metodo = SelectField("Método de pago",
                         choices=[("tarjeta_credito", "Tarjeta de crédito"),
                                  ("tarjeta_debito", "Tarjeta de débito"),
                                  ("transferencia", "Transferencia"),
                                  ("efectivo", "Efectivo")])
    resultado = SelectField("Resultado a simular",
                            choices=[("aprobado", "Pago aprobado"),
                                     ("rechazado", "Pago rechazado")])
    submit = SubmitField("Confirmar pago")

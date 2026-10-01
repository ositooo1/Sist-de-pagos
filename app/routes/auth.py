from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import db
from app.models import Usuario
from app.forms import RegistroForm, LoginForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    """Registra un usuario nuevo."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistroForm()
    if form.validate_on_submit():
        usuario = Usuario(nombre=form.nombre.data, email=form.email.data.lower())
        usuario.set_password(form.password.data)
        db.session.add(usuario)
        db.session.commit()
        flash("Cuenta creada. Ya podés iniciar sesión.", "success")
        return redirect(url_for("auth.login"))
    return render_template("registro.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Inicia sesión."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data.lower()).first()
        if usuario and usuario.check_password(form.password.data):
            login_user(usuario)
            siguiente = request.args.get("next")
            # solo redirige a rutas internas (evita redirecciones a sitios externos)
            if siguiente and urlparse(siguiente).netloc == "":
                return redirect(siguiente)
            return redirect(url_for("index"))
        flash("Email o contraseña incorrectos.", "danger")
    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    """Cierra la sesión."""
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))

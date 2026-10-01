from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Producto
from app.forms import ProductoForm, EliminarForm

products_bp = Blueprint("products", __name__, url_prefix="/productos")


@products_bp.route("/")
def listar():
    """Lista todos los productos (público)."""
    productos = Producto.query.order_by(Producto.nombre).all()
    return render_template(
        "productos.html", productos=productos, form_eliminar=EliminarForm()
    )


@products_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    """Crea un producto."""
    form = ProductoForm()
    if form.validate_on_submit():
        producto = Producto(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            precio=form.precio.data,
            stock=form.stock.data,
        )
        db.session.add(producto)
        db.session.commit()
        flash("Producto creado.", "success")
        return redirect(url_for("products.listar"))
    return render_template("producto_form.html", form=form, titulo="Nuevo producto")


@products_bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar(id):
    """Edita un producto existente."""
    producto = db.get_or_404(Producto, id)
    form = ProductoForm(obj=producto)  # precarga los datos en el formulario
    if form.validate_on_submit():
        form.populate_obj(producto)
        db.session.commit()
        flash("Producto actualizado.", "success")
        return redirect(url_for("products.listar"))
    return render_template("producto_form.html", form=form, titulo="Editar producto")


@products_bp.route("/<int:id>/eliminar", methods=["POST"])
@login_required
def eliminar(id):
    """Elimina un producto (solo por POST, con token CSRF)."""
    if not EliminarForm().validate_on_submit():
        flash("Solicitud inválida.", "danger")
        return redirect(url_for("products.listar"))
    producto = db.get_or_404(Producto, id)
    if producto.items:
        flash("No se puede eliminar: el producto ya figura en pedidos.", "warning")
    else:
        db.session.delete(producto)
        db.session.commit()
        flash("Producto eliminado.", "info")
    return redirect(url_for("products.listar"))

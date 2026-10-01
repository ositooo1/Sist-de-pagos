from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Producto, Pedido, ItemPedido
from app.forms import AccionForm

orders_bp = Blueprint("orders", __name__)


def _items_carrito():
    """Devuelve (lista de items, total) a partir del carrito guardado en sesión."""
    items, total = [], 0
    for pid, cantidad in session.get("carrito", {}).items():
        producto = db.session.get(Producto, int(pid))
        if producto:
            subtotal = producto.precio * cantidad
            items.append({"producto": producto, "cantidad": cantidad, "subtotal": subtotal})
            total += subtotal
    return items, total


@orders_bp.route("/carrito")
@login_required
def carrito():
    """Muestra el carrito actual."""
    items, total = _items_carrito()
    return render_template("carrito.html", items=items, total=total, form=AccionForm())


@orders_bp.route("/carrito/agregar/<int:id>", methods=["POST"])
@login_required
def agregar(id):
    """Agrega un producto al carrito."""
    if not AccionForm().validate_on_submit():
        abort(400)
    producto = db.get_or_404(Producto, id)
    try:
        cantidad = max(1, int(request.form.get("cantidad", 1)))
    except ValueError:
        cantidad = 1

    carrito = session.get("carrito", {})
    nueva = carrito.get(str(id), 0) + cantidad
    if nueva > producto.stock:
        flash(f"Stock insuficiente de {producto.nombre} (disponible: {producto.stock}).", "warning")
        return redirect(url_for("products.listar"))
    carrito[str(id)] = nueva
    session["carrito"] = carrito
    flash(f"{producto.nombre} agregado al carrito.", "success")
    return redirect(url_for("products.listar"))


@orders_bp.route("/carrito/quitar/<int:id>", methods=["POST"])
@login_required
def quitar(id):
    """Quita un producto del carrito."""
    if AccionForm().validate_on_submit():
        carrito = session.get("carrito", {})
        carrito.pop(str(id), None)
        session["carrito"] = carrito
    return redirect(url_for("orders.carrito"))


@orders_bp.route("/pedidos/confirmar", methods=["POST"])
@login_required
def confirmar():
    """Convierte el carrito en un pedido pendiente y descuenta el stock."""
    if not AccionForm().validate_on_submit():
        abort(400)
    items, total = _items_carrito()
    if not items:
        flash("El carrito está vacío.", "warning")
        return redirect(url_for("orders.carrito"))

    for it in items:
        if it["cantidad"] > it["producto"].stock:
            flash(f"Stock insuficiente de {it['producto'].nombre}.", "danger")
            return redirect(url_for("orders.carrito"))

    pedido = Pedido(usuario_id=current_user.id, estado="pendiente")
    for it in items:
        p = it["producto"]
        pedido.items.append(ItemPedido(producto_id=p.id, cantidad=it["cantidad"],
                                       precio_unitario=p.precio))
        p.stock -= it["cantidad"]
    pedido.calcular_total()
    db.session.add(pedido)
    db.session.commit()

    session.pop("carrito", None)
    flash("Pedido creado. Falta realizar el pago.", "success")
    return redirect(url_for("orders.detalle", id=pedido.id))


@orders_bp.route("/pedidos")
@login_required
def listar():
    """Lista los pedidos del usuario actual."""
    pedidos = (Pedido.query.filter_by(usuario_id=current_user.id)
               .order_by(Pedido.fecha.desc()).all())
    return render_template("pedidos.html", pedidos=pedidos)


@orders_bp.route("/pedidos/<int:id>")
@login_required
def detalle(id):
    """Detalle de un pedido (solo el dueño puede verlo)."""
    pedido = db.get_or_404(Pedido, id)
    if pedido.usuario_id != current_user.id:
        abort(403)
    return render_template("pedido_detalle.html", pedido=pedido, form=AccionForm())


@orders_bp.route("/pedidos/<int:id>/cancelar", methods=["POST"])
@login_required
def cancelar(id):
    """Cancela un pedido pendiente y devuelve el stock."""
    if not AccionForm().validate_on_submit():
        abort(400)
    pedido = db.get_or_404(Pedido, id)
    if pedido.usuario_id != current_user.id:
        abort(403)
    if pedido.estado != "pendiente":
        flash("Solo se pueden cancelar pedidos pendientes.", "warning")
    else:
        for it in pedido.items:
            it.producto.stock += it.cantidad
        pedido.estado = "cancelado"
        db.session.commit()
        flash("Pedido cancelado.", "info")
    return redirect(url_for("orders.detalle", id=pedido.id))

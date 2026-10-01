import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import Pedido, Pago
from app.forms import PagoForm, AccionForm

payments_bp = Blueprint("payments", __name__)


def _pedido_del_usuario(id):
    """Devuelve el pedido si pertenece al usuario actual; si no, 403."""
    pedido = db.get_or_404(Pedido, id)
    if pedido.usuario_id != current_user.id:
        abort(403)
    return pedido


@payments_bp.route("/pagos")
@login_required
def listar():
    """Historial de pagos y devoluciones del usuario."""
    pagos = (Pago.query.join(Pedido)
             .filter(Pedido.usuario_id == current_user.id)
             .order_by(Pago.fecha.desc()).all())
    return render_template("pagos.html", pagos=pagos)


@payments_bp.route("/pedidos/<int:id>/pagar", methods=["GET", "POST"])
@login_required
def pagar(id):
    """Simula el pago de un pedido y actualiza su estado."""
    pedido = _pedido_del_usuario(id)
    if pedido.estado not in ("pendiente", "rechazado"):
        flash("Este pedido no se puede pagar.", "warning")
        return redirect(url_for("orders.detalle", id=pedido.id))

    form = PagoForm()
    if form.validate_on_submit():
        pago = Pago(pedido_id=pedido.id, tipo="pago", monto=pedido.total,
                    metodo=form.metodo.data, estado=form.resultado.data,
                    id_externo="SIM-" + uuid.uuid4().hex[:10].upper())
        pedido.estado = "pagado" if form.resultado.data == "aprobado" else "rechazado"
        db.session.add(pago)
        db.session.commit()
        if pedido.estado == "pagado":
            flash("Pago aprobado. ¡Gracias por tu compra!", "success")
        else:
            flash("El pago fue rechazado. Podés intentar de nuevo.", "danger")
        return redirect(url_for("orders.detalle", id=pedido.id))
    return render_template("pagar.html", form=form, pedido=pedido)


@payments_bp.route("/pedidos/<int:id>/reembolsar", methods=["POST"])
@login_required
def reembolsar(id):
    """Simula la devolución de un pedido pagado y devuelve el stock."""
    if not AccionForm().validate_on_submit():
        abort(400)
    pedido = _pedido_del_usuario(id)
    if pedido.estado != "pagado":
        flash("Solo se pueden devolver pedidos pagados.", "warning")
        return redirect(url_for("orders.detalle", id=pedido.id))

    pago = Pago(pedido_id=pedido.id, tipo="reembolso", monto=pedido.total,
                metodo="simulado", estado="aprobado",
                id_externo="SIM-" + uuid.uuid4().hex[:10].upper())
    for it in pedido.items:
        it.producto.stock += it.cantidad
    pedido.estado = "reembolsado"
    db.session.add(pago)
    db.session.commit()
    flash("Devolución registrada y stock repuesto.", "info")
    return redirect(url_for("orders.detalle", id=pedido.id))

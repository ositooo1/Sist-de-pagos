import uuid
from decimal import Decimal
import mercadopago
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    abort,
    request,
    current_app,
)
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


def _sdk():
    """Crea el cliente de Mercado Pago, o None si falta el token."""
    token = current_app.config.get("MP_ACCESS_TOKEN")
    return mercadopago.SDK(token) if token else None


@payments_bp.route("/pagos")
@login_required
def listar():
    """Historial de pagos y devoluciones del usuario."""
    pagos = (
        Pago.query.join(Pedido)
        .filter(Pedido.usuario_id == current_user.id)
        .order_by(Pago.fecha.desc())
        .all()
    )
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
        pago = Pago(
            pedido_id=pedido.id,
            tipo="pago",
            monto=pedido.total,
            metodo=form.metodo.data,
            estado=form.resultado.data,
            id_externo="SIM-" + uuid.uuid4().hex[:10].upper(),
        )
        pedido.estado = "pagado" if form.resultado.data == "aprobado" else "rechazado"
        db.session.add(pago)
        db.session.commit()
        if pedido.estado == "pagado":
            flash("Pago aprobado. ¡Gracias por tu compra!", "success")
        else:
            flash("El pago fue rechazado. Podés intentar de nuevo.", "danger")
        return redirect(url_for("orders.detalle", id=pedido.id))
    return render_template("pagar.html", form=form, pedido=pedido)


@payments_bp.route("/pedidos/<int:id>/mercadopago", methods=["POST"])
@login_required
def mp_iniciar(id):
    """Crea una preferencia de Checkout Pro y redirige a Mercado Pago."""
    if not AccionForm().validate_on_submit():
        abort(400)
    pedido = _pedido_del_usuario(id)
    if pedido.estado not in ("pendiente", "rechazado"):
        flash("Este pedido no se puede pagar.", "warning")
        return redirect(url_for("orders.detalle", id=pedido.id))

    sdk = _sdk()
    if sdk is None:
        flash("Falta configurar MP_ACCESS_TOKEN en el archivo .env.", "danger")
        return redirect(url_for("orders.detalle", id=pedido.id))

    retorno = url_for("payments.mp_retorno", _external=True)
    datos = {
        "items": [
            {
                "title": it.producto.nombre,
                "quantity": it.cantidad,
                "unit_price": float(it.precio_unitario),
                "currency_id": "ARS",
            }
            for it in pedido.items
        ],
        "external_reference": str(pedido.id),
        "back_urls": {"success": retorno, "failure": retorno, "pending": retorno},
    }
    resp = sdk.preference().create(datos)
    if resp.get("status") not in (200, 201):
        current_app.logger.error("Error Mercado Pago: %s", resp)
        flash("No se pudo iniciar el pago con Mercado Pago. Revisá el token.", "danger")
        return redirect(url_for("orders.detalle", id=pedido.id))
    return redirect(resp["response"]["init_point"])


@payments_bp.route("/mercadopago/retorno")
@login_required
def mp_retorno():
    """Vuelta desde Mercado Pago: consulta el pago a la API y actualiza el pedido."""
    payment_id = request.args.get("payment_id") or request.args.get("collection_id")
    if not payment_id or payment_id == "null":
        flash("El pago no se completó.", "warning")
        return redirect(url_for("orders.listar"))

    sdk = _sdk()
    if sdk is None:
        abort(500)
    resp = sdk.payment().get(payment_id)
    if resp.get("status") != 200:
        flash("No se pudo verificar el pago con Mercado Pago.", "danger")
        return redirect(url_for("orders.listar"))
    info = resp["response"]

    try:
        pedido = _pedido_del_usuario(int(info.get("external_reference")))
    except (TypeError, ValueError):
        abort(400)

    if Decimal(str(info.get("transaction_amount", 0))) != Decimal(pedido.total):
        flash("El monto del pago no coincide con el pedido.", "danger")
        return redirect(url_for("orders.detalle", id=pedido.id))

    estado_mp = info.get("status")
    if estado_mp == "approved":
        estado_pago, estado_pedido = "aprobado", "pagado"
    elif estado_mp in ("rejected", "cancelled"):
        estado_pago, estado_pedido = "rechazado", "rechazado"
    else:
        estado_pago, estado_pedido = "pendiente", "pendiente"

    pago = Pago.query.filter_by(id_externo=str(payment_id)).first()
    if pago is None:
        pago = Pago(
            pedido_id=pedido.id,
            tipo="pago",
            monto=pedido.total,
            metodo="mp_" + str(info.get("payment_method_id", "mercadopago")),
            id_externo=str(payment_id),
        )
        db.session.add(pago)
    pago.estado = estado_pago
    if pedido.estado in ("pendiente", "rechazado"):
        pedido.estado = estado_pedido
    db.session.commit()

    mensajes = {
        "pagado": ("Pago aprobado en Mercado Pago. ¡Gracias por tu compra!", "success"),
        "rechazado": (
            "Mercado Pago rechazó el pago. Podés intentar de nuevo.",
            "danger",
        ),
        "pendiente": ("El pago quedó pendiente de acreditación.", "info"),
    }
    texto, categoria = mensajes[estado_pedido]
    flash(texto, categoria)
    return redirect(url_for("orders.detalle", id=pedido.id))


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

    pago = Pago(
        pedido_id=pedido.id,
        tipo="reembolso",
        monto=pedido.total,
        metodo="simulado",
        estado="aprobado",
        id_externo="SIM-" + uuid.uuid4().hex[:10].upper(),
    )
    for it in pedido.items:
        it.producto.stock += it.cantidad
    pedido.estado = "reembolsado"
    db.session.add(pago)
    db.session.commit()
    flash("Devolución registrada y stock repuesto.", "info")
    return redirect(url_for("orders.detalle", id=pedido.id))

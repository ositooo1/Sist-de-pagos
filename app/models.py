from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class Usuario(UserMixin, db.Model):
    """Usuario registrado. Tiene muchos pedidos."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    pedidos = db.relationship("Pedido", back_populates="usuario", lazy=True)

    def set_password(self, password):
        """Guarda la contraseña hasheada (nunca en texto plano)."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica una contraseña contra el hash guardado."""
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def cargar_usuario(user_id):
    """Flask-Login usa esta función para recuperar al usuario de la sesión."""
    return db.session.get(Usuario, int(user_id))


class Producto(db.Model):
    """Producto del catálogo."""

    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)

    items = db.relationship("ItemPedido", back_populates="producto", lazy=True)


class Pedido(db.Model):
    """Pedido de un usuario. Estados: pendiente, pagado, rechazado, cancelado."""

    __tablename__ = "pedidos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    estado = db.Column(db.String(20), nullable=False, default="pendiente")

    usuario = db.relationship("Usuario", back_populates="pedidos")
    items = db.relationship(
        "ItemPedido", back_populates="pedido", cascade="all, delete-orphan", lazy=True
    )
    pagos = db.relationship(
        "Pago", back_populates="pedido", cascade="all, delete-orphan", lazy=True
    )

    def calcular_total(self):
        """Suma subtotales de todos los ítems y actualiza el total."""
        self.total = sum(item.subtotal() for item in self.items)
        return self.total


class ItemPedido(db.Model):
    """Línea de un pedido: qué producto, cuántas unidades y a qué precio."""

    __tablename__ = "items_pedido"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)  # precio al comprar

    pedido = db.relationship("Pedido", back_populates="items")
    producto = db.relationship("Producto", back_populates="items")

    def subtotal(self):
        return self.precio_unitario * self.cantidad


class Pago(db.Model):
    """Intento de pago o cobro asociado a un pedido.

    tipo: 'pago' o 'cobro'
    estado: pendiente, aprobado, rechazado
    id_externo: reservado para el ID de Mercado Pago más adelante.
    """

    __tablename__ = "pagos"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    tipo = db.Column(db.String(10), nullable=False, default="pago")
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    metodo = db.Column(db.String(30), default="simulado")
    estado = db.Column(db.String(20), nullable=False, default="pendiente")
    id_externo = db.Column(db.String(100))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    pedido = db.relationship("Pedido", back_populates="pagos")

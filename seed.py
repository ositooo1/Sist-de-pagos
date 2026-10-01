from app import create_app, db
from app.models import Usuario, Producto

app = create_app()

with app.app_context():
    if Producto.query.count() == 0:
        db.session.add_all(
            [
                Producto(
                    nombre="Auriculares Bluetooth",
                    descripcion="Inalámbricos, 20h de batería",
                    precio=25000,
                    stock=15,
                ),
                Producto(
                    nombre="Teclado Mecánico",
                    descripcion="Switch rojo, retroiluminado",
                    precio=48000,
                    stock=10,
                ),
                Producto(
                    nombre="Mouse Gamer",
                    descripcion="RGB, 6 botones",
                    precio=18000,
                    stock=20,
                ),
                Producto(
                    nombre="Cargador USB-C 30W",
                    descripcion="Carga rápida",
                    precio=9500,
                    stock=30,
                ),
                Producto(
                    nombre="Webcam Full HD",
                    descripcion="1080p con micrófono",
                    precio=32000,
                    stock=8,
                ),
            ]
        )

    if not Usuario.query.filter_by(email="admin@test.com").first():
        admin = Usuario(nombre="Admin", email="admin@test.com")
        admin.set_password("admin123")
        db.session.add(admin)

    db.session.commit()
    print("Datos de prueba cargados.")

# Sist-de-pagos

# Sistema de pagos

Proyecto web desarrollado con **Python y Flask** para gestionar productos y pedidos y simular pagos.

## Funcionalidades

- Registro e inicio de sesión de usuarios.
- Gestión de productos.
- Carrito de compras y creación de pedidos.
- Simulación de pagos aprobados o rechazados.
- Actualización del estado de los pedidos.
- Integración opcional con Mercado Pago.

## Tecnologías

Python, Flask, Flask-Login, Flask-WTF, SQLAlchemy, SQLite y Jinja2.

## Instalación y ejecución

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

Preparar los datos de prueba:

```bash
python seed.py
```

Iniciar la aplicación:

```bash
python run.py
```

Luego, abrir en el navegador la dirección local que indique Flask, normalmente `http://127.0.0.1:5000`.

## Mercado Pago

La integración con Mercado Pago requiere credenciales configuradas localmente. Para probar el simulador local no se debe realizar un pago real. No incluir tokens privados en el repositorio.

## Estructura

- `app/`: rutas, modelos, formularios y plantillas.
- `run.py`: inicio de la aplicación.
- `config.py`: configuración.
- `requirements.txt`: dependencias.
- `seed.py`: datos de prueba.

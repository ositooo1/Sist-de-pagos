import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    """Configuración general de la aplicación."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "clave-de-desarrollo-cambiar")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")

import sys
import os
from app import create_app, db
from app.models import Plato, Ensalada, Combinacion

# Establecer la raíz del proyecto como el directorio de trabajo
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Crear la aplicación Flask
app = create_app()

# Ejecutar dentro de un contexto de aplicación
with app.app_context():
    combinaciones = [
        Combinacion(dia='domingo'),
        Combinacion(dia='lunes'),
        Combinacion(dia='martes'),
        Combinacion(dia='miércoles'),
        Combinacion(dia='jueves'),
        Combinacion(dia='viernes'),
        Combinacion(dia='sábado'),
    ]

    db.session.bulk_save_objects(combinaciones)
    db.session.commit()

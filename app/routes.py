from flask import render_template, request, redirect, url_for
from . import db
from .models import Plato, Ensalada, Combinacion
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from colorama import Fore, Style
from pytz import timezone, UTC
import inspect
import random
import pytz

colors = [Fore.CYAN, Fore.GREEN]
last_color = None

def printn(message):
    global last_color
    frame = inspect.currentframe()
    info = inspect.getframeinfo(frame.f_back)
    new_color = random.choice([color for color in colors if color != last_color])
    last_color = new_color
    print(f"{new_color}[{info.lineno - 1}] {message}{Style.RESET_ALL}")

def process_datetime(client_timezone, datetime_obj):
    client_tz = pytz.timezone(client_timezone)
    client_datetime_tz = client_tz.localize(datetime_obj)
    client_datetime_utc = client_datetime_tz.astimezone(pytz.utc)   
    client_datetime_local = client_datetime_utc.astimezone(client_tz)
    date_local=client_datetime_local.isoformat()
    utc_iso_format = client_datetime_utc.isoformat()
    return date_local, utc_iso_format


def register_routes(app):
    @app.route('/')
    def index():
        dias_esp = {
            'Monday': 'lunes',
            'Tuesday': 'martes',
            'Wednesday': 'miércoles',
            'Thursday': 'jueves',
            'Friday': 'viernes',
            'Saturday': 'sábado',
            'Sunday': 'domingo'
        }
        dia = datetime.now()
        dia_nombre = dia.strftime('%A')
        printn(dia_nombre)
        dia_nombre_esp = dias_esp.get(dia_nombre, dia_nombre)
        # dia_nombre_esp = 'jueves'
        dia_numero = dia.day
        dia_completo = f"{dia_nombre_esp} {dia_numero}"
        combinacion_obj = Combinacion.query.filter_by(dia=dia_nombre_esp).first()

        if combinacion_obj:
            plato_nombre = combinacion_obj.platos.nombre if combinacion_obj.platos else None
            ensalada_nombre = combinacion_obj.ensaladas.nombre if combinacion_obj.ensaladas else None
            ingredientes = combinacion_obj.platos.ingredientes if combinacion_obj.platos else []
            preparacion = combinacion_obj.platos.preparacion if combinacion_obj.platos else None
            imagen_relativa = combinacion_obj.platos.imagen if combinacion_obj.platos else None

            imagen_url = url_for('static', filename=imagen_relativa) if imagen_relativa else None
        else:
            plato_nombre = None
            ensalada_nombre = None
            ingredientes = []
            preparacion = None
            imagen_url = None

        return render_template(
        "index.html",
        dia=dia_completo,
        plato=plato_nombre,
        ensalada=ensalada_nombre,
        ingredientes=ingredientes,
        preparacion=preparacion,
        imagen=imagen_url
    )


    # @app.route('/usuarios')
    # def listar_usuarios():
    #     usuarios = Usuario.query.all()  # Obtener todos los usuarios desde la base de datos
    #     return render_template('usuarios.html', usuarios=usuarios)  # Renderizar la plantilla

    # # Ruta para agregar un nuevo usuario
    # @app.route('/usuarios/nuevo', methods=['GET', 'POST'])
    # def agregar_usuario():
    #     if request.method == 'POST':
    #         nombre = request.form['nombre']
    #         apellido = request.form['apellido']
    #         rut = request.form['rut']
    #         email = request.form['email']
    #         telefono = request.form['telefono']
            
    #         # Crear y guardar un nuevo usuario en la base de datos
    #         nuevo_usuario = Usuario(nombre=nombre, apellido=apellido, rut=rut, email=email, telefono=telefono)
    #         db.session.add(nuevo_usuario)
    #         db.session.commit()
            
    #         return redirect(url_for('listar_usuarios'))  # Redirigir a la lista de usuarios

    #     return render_template('nuevo_usuario.html')  # Mostrar el formulario de nuevo usuario

    # # Ruta para ver los detalles de una cita
    # @app.route('/citas/<int:cita_id>')
    # def ver_cita(cita_id):
    #     cita = Cita.query.get_or_404(cita_id)  # Obtener la cita por ID
    #     return render_template('detalle_cita.html', cita=cita)

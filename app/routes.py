from flask import render_template, request, redirect, url_for
from . import db
from .models import Plato, Combinacion, Carbohidrato
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

# def process_datetime(client_timezone, datetime_obj):
#     client_tz = pytz.timezone(client_timezone)
#     client_datetime_tz = client_tz.localize(datetime_obj)
#     client_datetime_utc = client_datetime_tz.astimezone(pytz.utc)   
#     client_datetime_local = client_datetime_utc.astimezone(client_tz)
#     date_local=client_datetime_local.isoformat()
#     utc_iso_format = client_datetime_utc.isoformat()
#     return date_local, utc_iso_format

def register_routes(app):
    @app.route('/week')
    def week():
        combinaciones_obj = Combinacion.query.order_by(Combinacion.id).all()
        
        dias_data = []
        for combinacion in combinaciones_obj:
            dia_info = {
                "dia": combinacion.dia,
                "plato_nombre": combinacion.platos.nombre if combinacion.platos else None,
                "ensalada_nombre": combinacion.ensaladas.nombre if combinacion.ensaladas else None,
                "plato_imagen": combinacion.platos.imagen if combinacion.platos else None,
                "plato_ingredientes": combinacion.platos.ingredientes if combinacion.platos else None,
                "plato_preparacion": combinacion.platos.preparacion if combinacion.platos else None,
            }
            dias_data.append(dia_info)
        
        return render_template("week.html", dias_data=dias_data)

    
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
        # printn(dia_nombre)
        dia_nombre_esp = dias_esp.get(dia_nombre, dia_nombre)
        # dia_nombre_esp = 'viernes'
        dia_numero = dia.day
        dia_completo = f"{dia_nombre_esp} {dia_numero}"
        
        if dia_nombre_esp == 'martes' or dia_nombre_esp == 'viernes':
            hoy = datetime.now().date() # <--- para aislar solo la fecha
            combinacion_obj = Combinacion.query.filter_by(dia=dia_nombre_esp).first()
            ultima_fecha_martes = combinacion_obj.fecha.date() # <--- aislar la fecha
            if ultima_fecha_martes == hoy:
                printn("ya se registró un plato hoy")
            else:
                carbohidratos_obj = Carbohidrato.query.all()
                if not carbohidratos_obj:
                    platos_con_carbohidratos = Plato.query.filter_by(tiene_carbos=True).all()
                    for plato in platos_con_carbohidratos:
                        nuevo_carbo = Carbohidrato(plato_id=plato.id)
                        db.session.add(nuevo_carbo)
                    db.session.commit()
               
                carbo_seleccionado = Carbohidrato.query.order_by(Carbohidrato.plato_id.asc()).first()
                plato = Combinacion.query.filter_by(dia=dia_nombre_esp).first()
                plato.plato_id = carbo_seleccionado.plato_id
                plato.fecha = datetime.now()
                db.session.delete(carbo_seleccionado)
                db.session.commit()
                    
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

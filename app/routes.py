from flask import render_template, request, redirect, url_for, jsonify
from . import db
from .models import Plato, Combinacion, Carbohidrato, PlatoIngrediente
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import json
import pprint

from .utils.debugging import printn

def register_routes(app):
    @app.route('/ingredients')
    def ingredients():
        '''
        - Iterar PlatoIngrediente
        - Si plato está en Combinacion, añadir ingrediente a lista_ingredientes considerando 'ingrediente', 'cantidad', 'unidad' y disponibilidad.
        
        - Iterar lista_ingredientes
        - Agregar a resultados nuevos ingredientes
        - Si el ingrediente ya está en resultados, sumar cantidades.
        '''
        combinaciones = Combinacion.query.order_by(Combinacion.id).all()
        plato_ingredientes = PlatoIngrediente.query.order_by(PlatoIngrediente.plato_id).all()

        lista_ingredientes = []

        for plato_ingrediente in plato_ingredientes:
            for combinacion in combinaciones:
                if plato_ingrediente.plato_id == combinacion.plato_id:
                    lista_ingredientes.append({
                        'id': plato_ingrediente.id,
                        'ingrediente': plato_ingrediente.ingredientes.nombre,
                        'cantidad': plato_ingrediente.cantidad,
                        'unidad': plato_ingrediente.unidades.unidad,
                        'disponibilidad': plato_ingrediente.disponible
                    })
                    break
        
        resultados = []

        for ingrediente in lista_ingredientes:
            encontrado = False

            for resultado in resultados:
                if resultado['ingrediente'] == ingrediente['ingrediente'] and resultado['unidad'] == ingrediente['unidad']:
                    resultado['cantidad'] += ingrediente['cantidad']
                    encontrado = True
                    break

            if not encontrado:
                resultados.append({
                    'id': ingrediente['id'],
                    'ingrediente': ingrediente['ingrediente'],
                    'cantidad': ingrediente['cantidad'],
                    'unidad': ingrediente['unidad'],
                    'disponibilidad': ingrediente['disponibilidad']
                })
        
        resultados.sort(key=lambda ing: (ing["unidad"] in ['cda', 'poco', 'chorrito', 'diente', 'cdita'], ing["ingrediente"]))

        # pprint.pprint(resultados)

        return render_template("total_ingredients.html", resultados=resultados)
    
    @app.route('/cambiar_estado/<item_id>', methods=["POST"])
    def cambiar_estado(item_id):
        item_obj = PlatoIngrediente.query.filter_by(id=item_id).first()
        
        if item_obj:
            print(f"Changing state for item with id: {item_id}, current state: {item_obj.disponible}")
            item_obj.disponible = not item_obj.disponible
            db.session.commit()
            return jsonify({"success": True, "new_state": item_obj.disponible})
        return jsonify({"success": False, "error": "Item no encontrado"}), 404


    @app.route('/week')
    def week():
        today = datetime.now()
        dias_semana = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado']
        inicio_semana = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today
        dias_con_fechas = []

        for i, dia in enumerate(dias_semana):
            fecha = inicio_semana + timedelta(days=i)
            dias_con_fechas.append({"dia": dia, "fecha": fecha.day})
        
        combinaciones_obj = Combinacion.query.order_by(Combinacion.id).all()
        
        dias_data = []
        for i, combinacion in enumerate(combinaciones_obj):
            plato_ingredientes = []
    
            if combinacion.platos:
                for plato_ingrediente in combinacion.platos.plato_ingredientes:
                    ingrediente = plato_ingrediente.ingredientes
                    plato_ingredientes.append({
                        "nombre": ingrediente.nombre,
                        "cantidad": plato_ingrediente.cantidad,
                        "unidad": plato_ingrediente.unidades.unidad
                    })
            dia_info = {
                "dia": dias_con_fechas[i]["dia"],  
                "fecha": dias_con_fechas[i]["fecha"], 
                "plato_nombre": combinacion.platos.nombre if combinacion.platos else None,
                "ensalada_nombre": combinacion.ensaladas.nombre if combinacion.ensaladas else None,
                "plato_imagen": combinacion.platos.imagen if combinacion.platos else None,
                "plato_ingredientes": plato_ingredientes,
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
        # dia = datetime(2025, 1, 19, 0, 0, 0)
        dia_nombre = dia.strftime('%A')
        dia_nombre_esp = dias_esp.get(dia_nombre, dia_nombre)
        # dia_nombre_esp = 'domingo'
        dia_numero = dia.day
        dia_completo = f"{dia_nombre_esp} {dia_numero}"
        
        if dia_nombre_esp == 'domingo':
            hoy = datetime.now().date() # <--- para aislar solo la fecha
            domingo_obj = Combinacion.query.filter_by(dia='domingo').first()
            ultima_fecha_domingo = domingo_obj.fecha.date() # <--- aislar la fecha
            if ultima_fecha_domingo == hoy:
                printn("ya se registraron los platos para martes y viernes")
            else:
                carbohidratos_obj = Carbohidrato.query.all()
                if not carbohidratos_obj:
                    platos_con_carbohidratos = Plato.query.filter_by(tiene_carbos=True).all()
                    for plato in platos_con_carbohidratos:
                        nuevo_carbo = Carbohidrato(plato_id=plato.id)
                        db.session.add(nuevo_carbo)
                    db.session.commit()

                dias = ['martes', 'viernes']

                for dia in dias:
                    carbo_seleccionado = Carbohidrato.query.order_by(Carbohidrato.plato_id.asc()).first()
                    plato = Combinacion.query.filter_by(dia=dia).first()
                    plato.plato_id = carbo_seleccionado.plato_id
                    db.session.delete(carbo_seleccionado)
                    db.session.commit()

                domingo_obj.fecha = datetime.now()
                db.session.commit()
                    
        combinacion_obj = Combinacion.query.filter_by(dia=dia_nombre_esp).first()

        if combinacion_obj:
            plato_nombre = combinacion_obj.platos.nombre if combinacion_obj.platos else None
            ensalada_nombre = combinacion_obj.ensaladas.nombre if combinacion_obj.ensaladas else None

            ingredientes = []

            if combinacion_obj.platos:
                for plato_ingrediente in combinacion_obj.platos.plato_ingredientes:
                    ingredientes.append({
                        "nombre": plato_ingrediente.ingredientes.nombre,
                        "cantidad": plato_ingrediente.cantidad,         
                        "unidad": plato_ingrediente.unidades.unidad     
                    })

            preparacion = combinacion_obj.platos.preparacion if combinacion_obj.platos else None
            imagen_relativa = combinacion_obj.platos.imagen if combinacion_obj.platos else None
            imagen_url = url_for('static', filename=imagen_relativa) if imagen_relativa else None

        else:
            plato_nombre = None
            ensalada_nombre = None
            ingredientes = None
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
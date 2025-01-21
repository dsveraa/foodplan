from flask import render_template, request, redirect, url_for, jsonify, session, flash
from sqlalchemy import desc
from . import db
from .models import Plato, Ensalada, Combinacion, Carbohidrato, PlatoIngrediente, Ingrediente, Unidad
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
import pprint
import os

from .utils.debugging import printn
from .utils.get_static_url import get_static_url as gsu
from .utils.image_processing import allowed_file

def register_routes(app):
    
    @app.route('/upload', methods=['POST'])
    def upload():
        if 'file' not in request.files:
            flash('No llegó la imagen', 'danger')
        file = request.files['file']
        
        if file.filename == '':
            flash('No se seleccionó un archivo', 'warning')
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('La imagen se subió correctamente', 'success')
            printn(filename)
            session['imagen_plato'] = filename
        return redirect(url_for('new_plate'))

    
    @app.route('/new_plate', methods=['GET', 'POST'])
    def new_plate():
        if request.method == 'POST':
            session['datos_plato'] = request.form.to_dict()
            return redirect(url_for('add_ingredients'))
        return render_template("new_plate.html")
    
    @app.route('/add_ingredients', methods=['GET', 'POST'])
    def add_ingredients():
        ingredientes_obj = Ingrediente.query.order_by(Ingrediente.nombre).all()
        unidades_obj = Unidad.query.order_by(Unidad.unidad).all()

        ingredientes = [{'id': ingrediente.id, 'nombre': ingrediente.nombre} for ingrediente in ingredientes_obj]
        unidades = [{'id': unidad.id, 'unidad':unidad.unidad} for unidad in unidades_obj]

        datos_plato = session.get('datos_plato', {})

        if request.method == 'POST':
            ingredientes_id = request.form.getlist('ingrediente_id[]')
            ingredientes_cantidad = request.form.getlist('ingrediente_cantidad[]')
            ingredientes_unidad = request.form.getlist('ingrediente_unidad[]')

            ingredientes = []
            for i in range(len(ingredientes_id)):
                ingredientes.append({
                    'id': ingredientes_id[i],
                    'cantidad': ingredientes_cantidad[i],
                    'unidad': ingredientes_unidad[i]
                })

            session['ingredientes'] = ingredientes

            datos_combinados = {**datos_plato, 'ingredientes': ingredientes}

            plato_nombre = datos_combinados['plato_nombre']
            plato_preparacion = datos_combinados['preparacion']
            plato_carbohidratos = datos_combinados['carbohidratos']
            plato_ingredientes = datos_combinados['ingredientes']

            imagen = session['imagen_plato']

            nuevo_plato = Plato(
                nombre=plato_nombre,
                preparacion=plato_preparacion, 
                imagen=f'images/{imagen}', 
                tiene_carbos=plato_carbohidratos == 'true')

            db.session.add(nuevo_plato)
            db.session.commit()

            ultimo_id_plato = nuevo_plato.id

            ingredientes = [
                PlatoIngrediente(
                    plato_id=ultimo_id_plato, 
                    ingrediente_id=ingrediente['id'], 
                    cantidad=ingrediente['cantidad'], 
                    unidad_id=ingrediente['unidad']
                ) 
                for ingrediente in plato_ingredientes
            ]
            db.session.bulk_save_objects(ingredientes)
            db.session.commit()


            return f'Datos combinados: {datos_combinados}'
        return render_template('add_ingredients.html', step1_data=datos_plato, ingredientes=ingredientes, unidades=unidades)
   
    @app.route('/change_combination', methods=['POST'])
    def change_combination():
        '''
        - recibir id de plato
        - recibir id de ensalada
        - recibir id de día
        - modificar columnas de Combinacion según esos datos
        '''
        dia_id = request.form.get('dia_id')
        plato_id = request.form.get('plato_id')
        ensalada_id = request.form.get('ensalada_id')

        combinacion = Combinacion.query.get(dia_id)

        combinacion.plato_id = plato_id
        combinacion.ensalada_id = ensalada_id
        db.session.commit()

        return redirect("week")
        # return jsonify({'message': f'Nuevo plato asignado al día {combinacion.dia}','plato': combinacion.platos.nombre}), 200

    @app.route('/combination/<combinacion_id>')
    def combination(combinacion_id):
        '''
        - listar platos
        - listar ensaladas
        - obtener combinación por id
        - seleccionar plato y ensalada
        - aplicar a combinación por id (/change_combination, methods=[POST])
        '''
        platos_obj = Plato.query.order_by(Plato.id).all()
        ensaladas_obj = Ensalada.query.order_by(Ensalada.id).all()
        combinacion_obj = Combinacion.query.get(combinacion_id)

        platos = [{'id': plato.id, 'nombre': plato.nombre} for plato in platos_obj]
        ensaladas = [{'id': ensalada.id, 'nombre': ensalada.nombre} for ensalada in ensaladas_obj]
        combinacion = {'id': combinacion_obj.id, 'plato': combinacion_obj.platos.nombre, 'ensalada': combinacion_obj.ensaladas.nombre, 'dia': combinacion_obj.dia, 'imagen': gsu(combinacion_obj.platos.imagen), 'plato_actual_id': combinacion_obj.plato_id, 'ensalada_actual_id': combinacion_obj.ensalada_id }

        return render_template("change_combination.html", platos=platos, ensaladas=ensaladas, combinacion=combinacion)
        # return jsonify({'platos': platos, 'ensaladas': ensaladas, 'combinacion': combinacion}), 200
    
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
                "plato_imagen": gsu(combinacion.platos.imagen) if combinacion.platos else None,
                "plato_ingredientes": plato_ingredientes,
                "plato_preparacion": combinacion.platos.preparacion if combinacion.platos else None,
                "id": combinacion.id
            }
            dias_data.append(dia_info)
        
        return render_template("week.html", dias_data=dias_data)
        # return jsonify({"dias_data": dias_data})

    
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
            imagen_url = gsu(combinacion_obj.platos.imagen)

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
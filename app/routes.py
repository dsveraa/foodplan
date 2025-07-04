from flask import render_template, request, redirect, url_for, jsonify, session, flash
from sqlalchemy import desc, and_, case
from sqlalchemy.orm import joinedload, with_loader_criteria
from collections import defaultdict
from . import db
from .models import Plato, Ensalada, Combinacion, PlatoIngrediente, User
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
import pprint
import os

from .utils.debugging import printn
from .utils.get_static_url import get_static_url as gsu
from .utils.image_processing import allowed_file
from app.services.helpers import (
    formatear_cantidad,
    map_porciones,
    mult_cantidad_ingrediente,
    obtener_dia_actual,
    obtener_detalles_combinacion,
    obtener_ingredientes,
    obtener_plato,
    obtener_plato_ingredientes,
    obtener_unidades,
    duplicar_PlatoIngrediente,
    duplicar_Combinaciones,
    redondear_a_decena_inferior
)

from .services.decorators import moderator_required

def register_routes(app):
    # @app.route("/set_password", methods=["GET", "POST"])
    # def set_password():
    #     user_id = 11
    #     user = User.query.filter_by(user_id=user_id)
    #     new_password = request.form['new_password']
    #     pass

    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        session.pop("username", None)
        return redirect(url_for("index"))
    
    @app.route('/register', methods=["GET", "POST"])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            repeat_password = request.form['repeat_password']

            if password != repeat_password:
                flash('Las contraseñas no coinciden', 'warning')
                return render_template("register.html", username=username)
            
            if User.query.filter_by(username=username).first():
                flash('El usuario ya existe', 'warning')
                return render_template("register.html", username=username)
            
            password_hash = generate_password_hash(password)

            new_user = User(username=username, password=password_hash)

            try:
                db.session.add(new_user)
                db.session.commit()
                flash('Usuario registrado correctamente', 'success')
                return redirect(url_for("login"))
            except Exception as e:
                db.session.rollback()
                flash(f'Error al registrar el usuario: {e}', 'danger')
                return render_template("register.html", username=username)
            
        return render_template("register.html")

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            try:
                user_obj = User.query.filter_by(username=username).first()

                if user_obj is None:
                    flash(f"El usuario '{username}' no existe todavía.", 'warning')
                    return render_template("login.html", username=username)
                    
                if not check_password_hash(user_obj.password, password):
                    flash(f"La contraseña para '{username}' es incorrecta.", 'danger')
                    return render_template("login.html", username=username)
                    
            except Exception as e:
                flash(f'Ocurrió un problema, intente nuevamente: {e}', 'danger')
                return render_template("login.html", username=username)
            
            session['user_id'] = user_obj.id
            session['username'] = user_obj.username
            session['role'] = user_obj.role

            user_id = session['user_id']

            existe_combinacion = Combinacion.query.filter_by(user_id=user_id).first()
            existe_platoIngrediente = PlatoIngrediente.query.filter_by(user_id=user_id).first()

            ref_uid = 1

            if not existe_platoIngrediente:
                duplicar_PlatoIngrediente(ref_uid, user_id)

            if not existe_combinacion:
                duplicar_Combinaciones(ref_uid, user_id)

            return redirect(url_for('index'))
        
        return render_template("login.html")


    @app.route('/edit_preparation/<id>', methods=["GET", "POST"])
    @moderator_required
    def edit_preparation(id):
        '''
        GET:

        - filtrar plato por id
        - obtener datos del plato desde tabla platos (nombre, preparación, imagen)

        POST:

        - reemplazar datos de preparación en tabla platos
        '''

        nombre, preparacion, imagen = obtener_plato(id)

        if request.method == 'POST':
            plato_obj = Plato.query.get_or_404(id)
            preparacion = request.form.get('preparacion')
            
            if preparacion:
                plato_obj.preparacion = preparacion
                db.session.commit()
            
            return redirect(url_for("week"))

        return render_template("edit_preparation.html", id=id, nombre=nombre, preparacion=preparacion, imagen=gsu(imagen))


    @app.route('/edit_ingredients/<id>', methods=["GET", "POST"])
    # @moderator_required
    def edit_ingredients(id):
        '''
        GET:

        - filtrar el plato por id
        - obtener datos del plato desde tabla platos (nombre, preparación)
        - obtener datos de ingredientes desde tabla plato_ingredientes (ingrediente_id, cantidad, unidad_id)
                
        POST:
        
        - si hay cambios en los valores de tabla platos, modificar tabla con nuevos valores.
        - si hay cambios en los valores de tabla plato_ingredientes, modificar con nuevos valores.
        - si hay nuevas entradas de ingredientes en tabla plato_ingredientes, agregar nuevos valores.
        '''
        
        nombre, preparacion, imagen = obtener_plato(id)
        plato_ingredientes = obtener_plato_ingredientes(id)
        ingredientes = obtener_ingredientes()
        unidades = obtener_unidades()

        user_id = session['user_id']

        if request.method == 'POST':
            ingredientes_id = request.form.getlist('ingrediente_id[]')
            ingredientes_cantidad = request.form.getlist('ingrediente_cantidad[]')
            ingredientes_unidad = request.form.getlist('ingrediente_unidad[]')
        
            plato_ingredientes = []
            for i in range(len(ingredientes_id)):
                plato_ingredientes.append({
                    'id': ingredientes_id[i],
                    'cantidad': ingredientes_cantidad[i],
                    'unidad': ingredientes_unidad[i]
                })
            
            antiguos_ingredientes = PlatoIngrediente.query.filter_by(plato_id=id, user_id=user_id).all()
            
            for ingrediente in antiguos_ingredientes:
                db.session.delete(ingrediente)

            ingredientes = [
                PlatoIngrediente(
                    plato_id=id, 
                    ingrediente_id=ingrediente['id'], 
                    cantidad=ingrediente['cantidad'], 
                    unidad_id=ingrediente['unidad'],
                    disponible=0,
                    user_id=user_id
                ) 
                for ingrediente in plato_ingredientes
            ]
            db.session.bulk_save_objects(ingredientes)
            db.session.commit()

            return redirect(url_for("week"))

        return render_template("edit_ingredients.html", id=id, nombre=nombre, preparacion=preparacion, imagen=gsu(imagen), plato_ingredientes=plato_ingredientes, ingredientes=ingredientes, unidades=unidades)
    
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
            session['datos_plato'] = request.form.to_dict() # {'plato_nombre': str, 'preparacion': str, 'carbohidratos': bool}
            datos_plato =  session['datos_plato']
            printn(datos_plato)
            return redirect(url_for('add_ingredients'))
        return render_template("new_plate.html")
    
    @app.route('/add_ingredients', methods=['GET', 'POST'])
    def add_ingredients():        
        ingredientes = obtener_ingredientes()
        unidades = obtener_unidades()

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

            from html import escape
            escaped_datos_combinados = {escape(str(key)): escape(str(value)) for key, value in datos_combinados.items()}
            return jsonify({'datos_combinados': escaped_datos_combinados})

        return render_template('add_ingredients.html', ingredientes=ingredientes, unidades=unidades)
   
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
        porciones = request.form.get('porciones')

        combinacion = Combinacion.query.get(dia_id)

        combinacion.plato_id = plato_id
        combinacion.ensalada_id = ensalada_id
        combinacion.porciones = porciones
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
        user_id = session.get("user_id")
        platos_obj = Plato.query.order_by(Plato.id).all()
        ensaladas_obj = Ensalada.query.order_by(Ensalada.id).all()
        combinacion_obj = Combinacion.query.get(combinacion_id)
        porciones_obj = Combinacion.query.filter_by(user_id=user_id)

        posibles_porciones = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        platos = [{'id': plato.id, 'nombre': plato.nombre} for plato in platos_obj]
        ensaladas = [{'id': ensalada.id, 'nombre': ensalada.nombre} for ensalada in ensaladas_obj]
        porciones = [porcion.porciones for porcion in porciones_obj]
        print(f"porciones: {porciones}")

        combinacion = {
            'id': combinacion_obj.id, 
            'plato': combinacion_obj.platos.nombre, 
            'ensalada': combinacion_obj.ensaladas.nombre, 
            'dia': combinacion_obj.dia, 
            'imagen': gsu(combinacion_obj.platos.imagen), 
            'plato_actual_id': combinacion_obj.plato_id, 
            'ensalada_actual_id': combinacion_obj.ensalada_id,
            'porciones': combinacion_obj.porciones
        }

        return render_template("change_combination.html", platos=platos, ensaladas=ensaladas, combinacion=combinacion, posibles_porciones=posibles_porciones)
    
    @app.route('/ingredients')
    def ingredients():
        '''
        - Iterar PlatoIngrediente
        - Si plato está en Combinacion, añadir ingrediente a lista_ingredientes considerando 'ingrediente', 'cantidad', 'unidad' y disponibilidad.
        
        - Iterar lista_ingredientes
        - Agregar a resultados nuevos ingredientes
        - Si el ingrediente ya está en resultados, sumar cantidades.
        '''
        
        if "username" not in session:
            return redirect(url_for('login'))
        
        user_id = session['user_id']

        # 1. Consulta las combinaciones y extrae sus multiplicadores
        dias_ordenados = case(
            (Combinacion.dia == "domingo", 1),
            (Combinacion.dia == "lunes", 2),
            (Combinacion.dia == "martes", 3),
            (Combinacion.dia == "miércoles", 4),
            (Combinacion.dia == "jueves", 5),
            (Combinacion.dia == "viernes", 6),
            (Combinacion.dia == "sábado", 7),
        )

        combinaciones_obj = Combinacion.query.filter_by(user_id=user_id).order_by(dias_ordenados).all()

        id_platos = [combinacion.plato_id for combinacion in combinaciones_obj]

        porciones = [combinacion.porciones for combinacion in combinaciones_obj]
        multiplicador = map_porciones(porciones)

        plato_ingredientes = (
            PlatoIngrediente.query
            .options(
                joinedload(PlatoIngrediente.ingredientes),
                joinedload(PlatoIngrediente.unidades),
            )
            .filter(
                and_(
                    PlatoIngrediente.user_id == user_id,
                    PlatoIngrediente.plato_id.in_(id_platos)
                )
            )
            .all()
        )

        lista_ingredientes = []

        for i, combinacion in enumerate(combinaciones_obj):
            plato_id_actual = combinacion.plato_id

            ingredientes_plato_actual = [
                pi for pi in plato_ingredientes 
                if pi.plato_id == plato_id_actual
            ]
            
            for plato_ingrediente in ingredientes_plato_actual:
                cantidad = mult_cantidad_ingrediente(
                    plato_ingrediente.cantidad, 
                    multiplicador[i], 
                    plato_ingrediente.unidades.unidad
                )
                
                lista_ingredientes.append({   
                    'id': plato_ingrediente.id,
                    'ingrediente': plato_ingrediente.ingredientes.nombre,
                    'cantidad': cantidad,
                    'unidad': plato_ingrediente.unidades.unidad,
                    'disponibilidad': plato_ingrediente.disponible
                })

        resultados = []
        for ingrediente in lista_ingredientes:
            encontrado = False
            for resultado in resultados:
                if (resultado['ingrediente'] == ingrediente['ingrediente'] and 
                    resultado['unidad'] == ingrediente['unidad']):
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

        for resultado in resultados:
            cantidad = resultado['cantidad']
            unidad = resultado['unidad']
            
            if unidad == 'g':
                cantidad = redondear_a_decena_inferior(cantidad)
            
            resultado['cantidad'] = formatear_cantidad(cantidad)

        resultados.sort(key=lambda ing: (ing["unidad"] in ['cda', 'poco', 'chorrito', 'diente', 'cdita'], ing["ingrediente"]))

        return render_template("total_ingredients.html", resultados=resultados)

    
    @app.route('/cambiar_estado/<item_id>', methods=["POST"])
    def cambiar_estado(item_id):
        if not session.get('user_id'):
            return jsonify({'error': 'Se necesita autenticación'}), 401
        
        item_obj = PlatoIngrediente.query.filter_by(id=item_id).first()
        
        if item_obj:
            print(f"Changing state for item with id: {item_id}, current state: {item_obj.disponible}")
            item_obj.disponible = not item_obj.disponible
            db.session.commit()
            return jsonify({"success": True, "new_state": item_obj.disponible})
        return jsonify({"success": False, "error": "Item no encontrado"}), 404

    @app.route('/week')
    def week():
        if "username" not in session:
            return redirect(url_for('login'))
        
        # ------------ esto es para obtener el día de la semana más la fecha calendario --------------
        
        today = datetime.now()
        dias_semana = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado']
        inicio_semana = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today
        dias_con_fechas = []

        for i, dia in enumerate(dias_semana):
            fecha = inicio_semana + timedelta(days=i)
            dias_con_fechas.append({"dia": dia, "fecha": fecha.day})
        
        # --------------------------------------------------------------------------------------------

        user_id = session.get('user_id')

        dias_ordenados = case(
            (Combinacion.dia == "domingo", 1),
            (Combinacion.dia == "lunes", 2),
            (Combinacion.dia == "martes", 3),
            (Combinacion.dia == "miércoles", 4),
            (Combinacion.dia == "jueves", 5),
            (Combinacion.dia == "viernes", 6),
            (Combinacion.dia == "sábado", 7),
        )

        combinaciones_obj = (
            Combinacion.query
            .options(
                joinedload(Combinacion.platos)
                .joinedload(Plato.plato_ingredientes) # <--
                .joinedload(PlatoIngrediente.ingredientes), # <--
                joinedload(Combinacion.ensaladas),
                with_loader_criteria(PlatoIngrediente, PlatoIngrediente.user_id == user_id)
            )
            .filter_by(user_id=user_id)
            .order_by(dias_ordenados)
            .all()
        )   
        
        porciones = [porcion.porciones for porcion in combinaciones_obj]
        
        multiplicador = map_porciones(porciones)
        
        dias_data = []
        for i, combinacion in enumerate(combinaciones_obj):
            plato_ingredientes = []
    
            if combinacion.platos:
                for plato_ingrediente in combinacion.platos.plato_ingredientes: # -->
                    ingrediente = plato_ingrediente.ingredientes # -->

                    cantidad = mult_cantidad_ingrediente(plato_ingrediente.cantidad, multiplicador[i], plato_ingrediente.unidades.unidad)
                    
                    if plato_ingrediente.unidades.unidad == 'g':
                        cantidad = redondear_a_decena_inferior(cantidad)
                                        
                    plato_ingredientes.append({
                        "nombre": ingrediente.nombre,
                        "cantidad": formatear_cantidad(cantidad), 
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
                "id": combinacion.id,
                "plato_id": combinacion.platos.id,
                "porciones": combinacion.porciones
            }
            dias_data.append(dia_info)
        
        return render_template("week.html", dias_data=dias_data)
        # return jsonify({"dias_data": dias_data})

    @app.route('/')
    def index():
        usuario = session.get('username')
        
        dia_nombre_esp, dia_numero = obtener_dia_actual()
        dia_completo = f"{dia_nombre_esp} {dia_numero}"

        # if dia_nombre_esp == 'domingo':
        #     manejar_domingo()

        plato, ensalada, ingredientes, preparacion, imagen = obtener_detalles_combinacion(dia_nombre_esp)

        # print(ingredientes)

        return render_template(
            "index.html",
            dia=dia_completo,
            plato=plato,
            ensalada=ensalada,
            ingredientes=ingredientes,
            preparacion=preparacion,
            imagen=imagen,
            user = usuario
        )
from datetime import datetime
from app.models import Combinacion, Carbohidrato, Plato, db, Ingrediente, Unidad, PlatoIngrediente, User
from app.utils.get_static_url import get_static_url as gsu
from flask import session

DIAS_ESP = {
    'Monday': 'lunes', 'Tuesday': 'martes', 'Wednesday': 'miércoles',
    'Thursday': 'jueves', 'Friday': 'viernes', 'Saturday': 'sábado', 'Sunday': 'domingo'
}

def obtener_dia_actual():
    """ Devuelve el nombre del día en español y su número. """
    dia = datetime.now()
    dia_nombre_esp = DIAS_ESP.get(dia.strftime('%A'), dia.strftime('%A'))
    # dia_nombre_esp = 'domingo'
    return dia_nombre_esp, dia.day

def manejar_domingo():
    """ Lógica para registrar platos en martes y viernes si es domingo. """
    hoy = datetime.now().date()
    domingo_obj = Combinacion.query.filter_by(dia='domingo').first()

    if not domingo_obj:
        return

    ultima_fecha_domingo = domingo_obj.fecha.date()

    if ultima_fecha_domingo == hoy:
        print("Ya se registraron los platos para martes y viernes")
        return

    hay_carbohidratos = Carbohidrato.query.all()

    if not hay_carbohidratos:
        platos_con_carbohidratos = Plato.query.filter_by(tiene_carbos=True).all()
        for plato in platos_con_carbohidratos:
            db.session.add(Carbohidrato(plato_id=plato.id))
        db.session.commit()

    # Asignar carbohidratos a martes y viernes
    for dia in ['martes', 'viernes']:
        carbo_seleccionado = Carbohidrato.query.order_by(Carbohidrato.plato_id.asc()).first()
        if carbo_seleccionado:
            plato = Combinacion.query.filter_by(dia=dia).first()
            if plato:
                plato.plato_id = carbo_seleccionado.plato_id
                db.session.delete(carbo_seleccionado)
                db.session.commit()

    domingo_obj.fecha = datetime.now()
    db.session.commit()

def obtener_detalles_combinacion(dia_nombre_esp):
    """ Obtiene detalles del plato, ensalada, ingredientes y preparación. """
    combinacion_obj = Combinacion.query.filter_by(dia=dia_nombre_esp).first()

    if not combinacion_obj:
        return None, None, None, None, None

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
    imagen_url = gsu(combinacion_obj.platos.imagen) if combinacion_obj.platos else None

    return plato_nombre, ensalada_nombre, ingredientes, preparacion, imagen_url

def obtener_ingredientes():
    ingredientes_obj = Ingrediente.query.order_by(Ingrediente.nombre).all()
    ingredientes = [{'id': ingrediente.id, 'nombre': ingrediente.nombre} for ingrediente in ingredientes_obj]

    return ingredientes

def obtener_unidades():
    unidades_obj = Unidad.query.order_by(Unidad.unidad).all()
    unidades = [{'id': unidad.id, 'unidad':unidad.unidad} for unidad in unidades_obj]

    return unidades

def obtener_plato(id):
    plato_obj = Plato.query.get(id)
    nombre = plato_obj.nombre
    preparacion = plato_obj.preparacion
    imagen = plato_obj.imagen

    return nombre, preparacion, imagen

def obtener_plato_ingredientes(id):
    '''
    - filtra los resultados por el id del plato y user_id
    - devuelve una lista de todos los atributos de la tabla en tantos diccionarios como ingredientes registra el plato.
    '''
    user_id = session['user_id']

    plato_ingredientes = PlatoIngrediente.query.filter_by(plato_id=id, user_id=user_id).all()
    plato_ingredientes = [{'id':ingrediente.id, 'ingrediente_id': ingrediente.ingrediente_id, 'nombre':ingrediente.ingredientes.nombre,'cantidad': ingrediente.cantidad, 'unidad_id': ingrediente.unidad_id, 'disponibilidad': ingrediente.disponible} for ingrediente in plato_ingredientes]

    return plato_ingredientes

def duplicar_PlatoIngrediente(ref_uid, user_id):
    registros_ref = PlatoIngrediente.query.filter_by(user_id=ref_uid).all()
    
    nuevos_registros = []
    for registro in registros_ref:
        nuevo_registro = PlatoIngrediente(
            plato_id=registro.plato_id,
            ingrediente_id=registro.ingrediente_id,
            cantidad=registro.cantidad,
            unidad_id=registro.unidad_id,
            disponible=registro.disponible,
            user_id=user_id
        )
        nuevos_registros.append(nuevo_registro)
    
    db.session.add_all(nuevos_registros)
    db.session.commit()

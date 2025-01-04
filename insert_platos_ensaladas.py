import sys
import os
from app import create_app, db
from app.models import Plato, Ensalada

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = create_app()

with app.app_context():
    platos = [
        Plato(
            nombre="Saltado de verduras con pollo",
            ingredientes="""1 brócoli pequeño picado
1 zapallito italiano en cubos
1 taza de coliflores
1/2 taza de porotos verdes
1 cda de jengibre
2 cda de salsa de tamarindo
Salsa de soya
Sal
Pimienta
Comino
3 cda de hinojo picado
Aceite""",
            preparacion="""Calentar un wok y agregar aceite, colocar jengibre, tamarindo e hinojo; dorar para luego incorporar pimienta y comino. Agregar las coliflores y revolver constantemente por 5 minutos. Añadir los brócolis y repetir el mismo proceso. Cuando las verduras estén al dente podemos incorporar los zapallitos italianos. Para terminar agregamos el poroto verde previamente cocido, sal, salsa de soya; mezclamos y retiramos del fuego."""
        ),
        Plato(
            nombre="Berenjenas empanizadas con escalopas",
            ingredientes="""1 berenjena grande
1 taza de pan rallado
1/2 cda de orégano seco
1/2 cda de sal
1/4 de cda de merquén
300 gr de tomate
2 cda de aceite de oliva
10 hojas de albahaca picada en tiras""",
            preparacion="""Precalentar el horno a 170° C. Cortar la berenjena en rebanadas del mismo ancho. Mezclar el pan, el orégano, la sal y el merquén. En cada berenjena poner un poco de aceite de oliva y pasarla por el pan molido. Poner sobre una lata engrasada. Meterlas al horno hasta que estén firme al tacto y doraditas; aproximadamente unos 45-50 minutos."""
        ),
        Plato(
            nombre="Garbanzos guisados",
            ingredientes="""1/2 kg de garbanzos
Aceite
Sal
Comino
2 cda de ají en cubitos
1 cda de curry
3 cda de cilantro molido
5 tomates
Orégano
4 cda de pimiento molido""",
            preparacion="""Hervir los garbanzos hasta que estén blandos. Dorar cilantro, ají y pimentón molido, agregar comino, sal, curry y por último los tomates picados, hasta que se haga una pasta. Luego mezclarlo con los garbanzos, cocinar por 5 minutos y agregar el orégano al retirar del fuego."""
        ),
        Plato(
            nombre="Espaguetis al pesto",
            ingredientes="""1 pqte de espaguetis
1/2 de espinacas
1 taza de albahaca
100 gr de queso
50 gr de castañas
1/2 taza de leche
Nuez moscada
Mantequilla""",
            preparacion="""Cocinar los espaguetis y reservarlos. Licuar la espinaca picada, albahaca, queso, castañas y leche. Derretir la mantequilla, vaciar el licuado encima y mover hasta que hierva, agregar sal, nuez moscada y pimienta. Apagar el fuego y servir encima de los espaguetis rallándoles queso parmesano encima."""
        ),
        Plato(
            nombre="Lasagna",
            ingredientes="""1 pqte de pasta para lasagna precocida
350 gr de carne molida
1/8 taza de salsa de soya
500 cc de salsa de tomate
2 tazas de salsa blanca
250 gr de queso fresco
1/2 cebolla""",
            preparacion="""Hacer la salsa con cebolla, carne, soya y salsa de tomate. Untar la base de lmode con salsa blanca. Armar por pisos con pasta y salsas más queso hasta llenar la fuente. Hornear 20 minutos."""
        ),
        Plato(
            nombre="Arroz al curry con espinaca",
            ingredientes="""1 vaso de arroz
2 vasos de agua
1 manojo de espinacas
1 puñado de nueces
Curry el polvo
Aceite de oliva""",
            preparacion="""Sofreír las nueces peladas, cuando estén doradas agregar el arroz y revolver. Añadir el agua caliente y luego las espinacas y por último el curry. Dejar a fuego lento hasta que esté listo."""
        )
    ]

    ensaladas = [
        Ensalada(nombre="Lechuga"),
        Ensalada(nombre="Tomate"),
        Ensalada(nombre="Poroto verde"),
        Ensalada(nombre="Brócoli")
    ]

    db.session.bulk_save_objects(platos)
    db.session.bulk_save_objects(ensaladas)
    db.session.commit()


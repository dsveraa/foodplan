from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship
from . import db

class Plato(db.Model):
    __tablename__ = 'platos'
    
    id = Column(Integer, primary_key=True)
    tiene_carbos = Column(Boolean, default=False)
    nombre = Column(String(100), nullable=False)
    preparacion = Column(Text, nullable=True)
    imagen = Column(String, nullable=True)

    combinaciones = relationship("Combinacion", back_populates="platos")
    plato_ingredientes = relationship("PlatoIngrediente", back_populates="platos")

class Ensalada(db.Model):
    __tablename__ = 'ensaladas'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)

    combinaciones = relationship("Combinacion", back_populates="ensaladas")

class Combinacion(db.Model):
    __tablename__ = 'combinaciones'
    
    id = Column(Integer, primary_key=True)
    dia = Column(String(20), nullable=True)
    plato_id = Column(Integer, ForeignKey('platos.id'), nullable=True)
    ensalada_id = Column(Integer, ForeignKey('ensaladas.id'), nullable=True)
    fecha = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    porciones = Column(Integer, default=3)

    platos = relationship("Plato", back_populates="combinaciones")
    ensaladas = relationship("Ensalada", back_populates="combinaciones")
    # users = relationship("User", back_populates="combinaciones", cascade='all, delete')

class Carbohidrato(db.Model):
    __tablename__ = 'carbohidratos'

    id = Column(Integer, primary_key=True)
    plato_id = Column(Integer, ForeignKey('platos.id'), nullable=True)
    
class Ingrediente(db.Model):
    __tablename__ = 'ingredientes'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=True)

    plato_ingredientes = relationship('PlatoIngrediente', back_populates='ingredientes')

class PlatoIngrediente(db.Model):
    __tablename__ = 'plato_ingredientes'

    id = Column(Integer, primary_key=True)
    plato_id = Column(Integer, ForeignKey('platos.id'), nullable=False)
    ingrediente_id = Column(Integer, ForeignKey('ingredientes.id'), nullable=False)
    cantidad = Column(Integer)
    unidad_id = Column(Integer, ForeignKey('unidades.id'), nullable=True)
    disponible = Column(Boolean, default=False, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))

    platos = relationship("Plato", back_populates="plato_ingredientes")
    ingredientes = relationship('Ingrediente', back_populates="plato_ingredientes")
    unidades = relationship("Unidad", back_populates="plato_ingredientes")


class Unidad(db.Model):
    __tablename__ = 'unidades'

    id = Column(Integer, primary_key=True)
    unidad = Column(String(10), nullable=True)

    plato_ingredientes = relationship("PlatoIngrediente", back_populates="unidades")

class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(20))
    password = Column(String(250))
    role = Column(String(20), default='user')

user = relationship("Combinacion", back_populates='user')
user = relationship("PlatoIngrediente", back_populates='user')
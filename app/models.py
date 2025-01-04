from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from . import db

class Plato(db.Model):
    __tablename__ = 'platos'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    ingredientes = Column(JSON, nullable=True)
    preparacion = Column(Text, nullable=True)
    imagen = Column(String, nullable=True)

    combinaciones = relationship("Combinacion", back_populates="platos")

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

    platos = relationship("Plato", back_populates="combinaciones")
    ensaladas = relationship("Ensalada", back_populates="combinaciones")

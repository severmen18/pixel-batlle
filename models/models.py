from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    '''
        Модель пользователя
    '''
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    vk_id = Column(String, unique = True)
    faculty = Column(String)
    point_count = Column(Integer)
    charges_count = Column(Integer) # количество оставшихся зарядов
    last_shot = Column(DateTime)
    skin = Column(Integer)
    user = relationship('Matrix')


class Matrix(Base):
    """
     Для матрицы пока размер 500x500
    """
    __tablename__ = "matrix"
    id = Column(Integer, primary_key=True)
    x_position = Column(Integer)
    y_position = Column(Integer)
    color = Column(String)
    user_point = Column(Integer, ForeignKey("user.id")) # пользователь который установил метку
    update_datetime = Column(DateTime)

class MyConsts(Base):
    '''
        класс для хранения настройки сервера
    '''

    __tablename__ = "my_consts"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(String)

    '''
        планируем хранить
        кол-во зарядов shot_count
        время на перезярядку recharge_time
    '''
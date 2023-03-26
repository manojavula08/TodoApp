from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Users(Base):
    __tablename__ = "users"
    email = Column(String, unique=True, index=True)
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    hash_password = Column(String)
    phone_number = Column(String)
    # address_id = Column(String, ForeignKey("address.id"), nullable=True)
    # address = relationship("Address", back_populates="user_address")
    todos = relationship("Todos", back_populates="users")


class Todos(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
    activity_type = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    users = relationship("Users", back_populates="todos")


class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    address1 = Column(String)
    city = Column(String)
    state = Column(String)
    apt_num = Column(String)
    # user_address = relationship("Users", back_populates="address")

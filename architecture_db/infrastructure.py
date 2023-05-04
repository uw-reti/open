from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, Table, create_engine 
from sqlalchemy.orm import relationship, backref, declarative_base,registry

Base = declarative_base()

system_association_table = Table('system_association', Base.metadata,
    Column('parent_id', Integer, ForeignKey('system.id')),
    Column('child_id', Integer, ForeignKey('system.id'))
)

requirement_association_table = Table('req_association', Base.metadata,
    Column('system_id', Integer, ForeignKey('system.id')),
    Column('requirement_id', Integer, ForeignKey('requirement.id'))
)

interface_association_table = Table('int_association', Base.metadata,
    Column('system_id', Integer, ForeignKey('system.id')),
    Column('interface_id', Integer, ForeignKey('interface.id')),
)

reactor_association_table  = Table('reac_association', Base.metadata,
    Column('system_id', Integer, ForeignKey('system.id')),
    Column('reactor_id', Integer, ForeignKey('reactor.id'))
)


class System(Base):
    __tablename__ = 'system'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    parent_id = Column(Integer, ForeignKey('system.id'))
    children = relationship("System",
        backref=backref('parent', remote_side=id),
        secondary=system_association_table,
        primaryjoin=id==system_association_table.c.parent_id,
        secondaryjoin=id==system_association_table.c.child_id,
        )
    requirements = relationship("Requirement", secondary=requirement_association_table, back_populates='systems')
    interfaces = relationship("Interface", secondary=interface_association_table, back_populates='systems')
    reactors = relationship("Reactor", secondary=reactor_association_table, back_populates='systems')


class Requirement(Base):
    __tablename__ = 'requirement'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    systems = relationship("System", secondary=requirement_association_table, back_populates='requirements')


class Interface(Base):
    __tablename__ = 'interface'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    systems = relationship("System", secondary=interface_association_table, back_populates='interfaces')
    
    #Nature of the interface. Only set things that need to be set
    temperature = Column(Float,default=None)
    power = Column(Float,default=None)
    volume = Column(Float,default=None)
    
    

class Reactor(Base):
    __tablename__ = 'reactor'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    systems = relationship("System", secondary=reactor_association_table, back_populates='reactors')

engine = create_engine('sqlite:///mydatabase2.db', echo=True)
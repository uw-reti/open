# -*- coding: utf-8 -*-
"""
Created on Thu Apr 27 07:55:45 2023

@author: b9801
"""

from sqlalchemy.orm import sessionmaker
from infrastructure import engine, System, Requirement, Interface, Reactor
import graphviz

colors=['#648FFF','#785EF0','#DC267F','#FE6100','#FFB000']

graph = graphviz.Digraph()

# Create a session factory
Session = sessionmaker(bind=engine)

# Create a session instance
session = Session()



for reactor_name in ['SFR','HTR','MSR']:
    
    graph = graphviz.Digraph(engine='fdp') #'sfdp'
    graph.graph_attr['splines'] = 'true'

    reactor=session.query(Reactor).filter_by(name=reactor_name).first()
    
    reactor_system_list=[]
    for system in reactor.systems:
        reactor_system_list.append(system.name)
        graph.node(system.name,shape='rectangle')
        
        for subsystem in system.children:
            graph.node(subsystem.name,shape='rectangle')
            graph.edge(system.name,subsystem.name,color=colors[0])
            reactor_system_list.append(subsystem.name)
        
    #Find all systems for which interfaces are present
    interfaces=session.query(Interface)
    for interface in interfaces:
        
        flag = True
        system_names=[]
        
        for system in interface.systems:
            if system.name in reactor_system_list:
                system_names.append(system.name)
            else:
                flag = False
                break 
            
        if flag:
            graph.edge(system_names[0],system_names[1],constraint='false',color=colors[1])
    
    graph.render('diagram_'+reactor_name,format='png')
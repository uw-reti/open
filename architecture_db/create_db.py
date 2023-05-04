# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 16:15:38 2023

@author: b9801


Basic idea here is to add everything that's in the draw.io for three reactor types. 
"""
from sqlalchemy.orm import sessionmaker
from infrastructure import System, Requirement, Interface, Reactor, Base, engine
import os

#registry.configure(engine) 
Base.metadata.create_all(engine)

# Create a session factory
Session = sessionmaker(bind=engine)

# Create a session instance
session = Session()

#TODO! Put this into github

systems={'Reactor Building':['Reactor Building Structure',
                            'Reactor Building Vents & Drain',
                            'RPV Supports',
                            'CRDMs',
                            'Cavity',
                            'Guard Vessel',
                            'In-vessel storage',
                            'Reactor Vessel Top Enclosure (Deck)',
                            'Deck Cooling and Insulation',
                            'Deck Shielding',
                            'Deck Support Structure',
                            'In service inspection'
                            'Off gas management system'],
        'Fuel Handling System':['Fuel Handling Machine',
                                'Gripper',
                                'Inter-building transport',
                                'Fuel Storage',
                                'Fuel Topup System',
                                'Burnup Measurement System'],
        'Plant Auxilliary Systems':['Exhaust Air Monitoring System',
                                    'Remote Maintanence System',
                                    'Fire Protection System',
                                    'Decontamination System',
                                    'Waste Handling System',
                                    'Physical Security System',
                                    'Spent Fuel Cooling System',
                                    'Component Cooling System',
                                    'HVAC systems',
                                    'New fuel store',
                                    'Hot workshop',
                                    'Laboratories',
                                    'Storage'],
        'Coolant Auxilliary Systems':{'SFR':['Reactor Vessel Heating Systems',
                                    'Guard and Thimble Cooling Systems',
                                    'Primary Sodium Purification System',
                                    'Auxilliary Liquid Metal System',
                                    'Inert Gas System'],
                                     'HTR':['Helium Purification System',
                                    'Helium Supply and Storage System',
                                    'Dump System for Helium Supporting Systems',
                                    'Gaseous Water Storage System',
                                    'Water Extraction System for Helium Storage System',
                                    'Gas Evacuation System for Primary System',
                                    'Gas Analysis System'],
                                    'MSR':['Tritium Management System',
                                    'Inert Gas Storage',
                                    'Chemistry Control System',
                                    'Inventory Management System']},
        'I&C Systems':['Reactor Protection System',
                        'Plant Control System',
                        'Main Control Room',
                        'Flux Monitoring System',
                        'Heat Transport Instrumentation System',
                        'Radiation Montioring System',
                        'Impurity Monitoring and Analysis',
                        'Data Handling and Signal Transmission System',
                        'Communications',
                        'Industry Security and Safeguards System'],
         'Decay Heat Removal Systems':['Reactor Cavity Cooling System',
                        'Shutdown Heat Removal System'],
         'Seismic Isolation System':[],
         'Reactor Pressure Vessel':['Fuel elements',
                        'Control systems',
                        'Core instrumentation and neutron sources',
                        'Core Restraint System',
                        'RPV Internals',
                        'Primary Pump',
                        'Cross Duct',
                        'Primary HX',
                        'Primary Circulator'],
         'Electrical Systems':['Plant AC',
                        'Essential AC',
                        'Essential DC',
                        'Plant DC',
                        'Backup Generators',
                        'Ground, Lightning Protection',
                        'Generator transformer',
                        'Short circuit limiter',
                        'Substation'],
         'Civils/Misc':['Car park',
                        'Security',
                        'Gatehouse',
                        'Operations Building',
                        'Bridge Sturcture',
                        'Roadway',
                        'Heavy Component Assembly Area',
                        'Fencing and Gates'],
         'Thermal Energy Storage':['Molten Salt storage tanks',
                        'TES Pump',
                        'Secondary HX',
                        'Piping',
                        'Control System'],
          'Brayton Power Conversion System':['Building System',
                        'Gas Turbine',
                        'Recuperator',
                        'Condensor',
                        'Circulator'],
          'Rankine Power Conversion System':['Building System',
                        'Steam Turbines',
                        'Feedwater Heaters',
                        'Condensor',
                        'PCS Pump'],
         'Intermediate Loop':['Intermediate Pump',
                        'Secondary HX',
                        'Piping',
                        'Storage Tank',
                        'Expansion Tank',
                        'Cleanup Systems',
                        'Sodium/water reaction protection']
         }

"""DECISIONS!
- HTR/SFR/MSR/FHR
- Size
- TES/no TES
- Coal Repowering (identifies systems that repower)
"""

#TODO! ATM it is adding every child systems x3 to every reactor
#TODO! Sort out which systems arent in each reactor (e.g. Gripper)

#TODO! Coal repower

#TODO: As we add the systems, define which reactors the systems go in? Then we can propagate system information through each of the three reactors

reactor_types=['SFR','HTR','MSR']

excluded_systems={}

for reactor_type in reactor_types:
    excluded_systems[reactor_type]=['Intermediate Loop','Brayton Power Conversion System']

excluded_systems['SFR']+=['Fuel Topup System','Off gas management system','Cross Duct','Primary Circulator']
excluded_systems['HTR']+=['Off gas management system','Guard Vessel','In-vessel storage','Primary Pump']
excluded_systems['MSR']+=['Fuel Topup System','Guard Vessel','In-vessel storage','Cross Duct','Primary Circulator']


for reactor_type in reactor_types:
    
    reactor=Reactor(name=reactor_type)
    session.add(reactor)
    
    excluded_systems[reactor_type]=['Intermediate Loop','Brayton Power Conversion System']

    for system_name in systems.keys():
        # Create a parent system
        if system_name not in excluded_systems[reactor_type]:
            parent_system = System(name=system_name,reactors=[reactor])
            session.add(parent_system)
            
            if system_name == 'Coolant Auxilliary Systems':
                child_systems = systems[system_name][reactor_type]
            else:
                child_systems = systems[system_name]
            
            for child_system in child_systems:
                if child_system not in excluded_systems[reactor_type]:
                    child_system = System(name=child_system,parent=[parent_system],reactors=[reactor])
                    session.add(child_system)
                    
    session.commit()

#Create a requirement and associate it with system
requirement = Requirement(name='Shall protect against aircraft crash')
these_systems = session.query(System).filter_by(name='Reactor Building Structure').all()
for this_system in these_systems:
    requirement.systems.append(this_system)
session.add(requirement)
session.commit()

#Example of a requirement on the building system that can propagate thr
requirement = Requirement(name='Shall provide a decontamination factor')
these_systems = session.query(System).filter_by(name='Reactor Building Vents & Drain').all()
for this_system in these_systems: #havent figured out how to do this by query. Does this system appear in non-HTRs?
    if this_system.reactors[0].name=='HTR':
        requirement.systems.append(this_system)
session.add(requirement)
session.commit()


interface_pairs=[('Reactor Building','Seismic Isolation System'),
                 ('Reactor Building','Plant Auxilliary Systems'),
                 ('Reactor Building','Fuel Handling System'),
                 ('Plant Auxilliary Systems','Coolant Auxilliary Systems'),
                 ('Reactor Building','Reactor Pressure Vessel'),
                 ('Reactor Building','I&C Systems'),
                 ('Reactor Pressure Vessel','Decay Heat Removal Systems'),
                 ('Reactor Building','Decay Heat Removal Systems'),
                 ('Reactor Pressure Vessel','Thermal Energy Storage'),
                 ('Thermal Energy Storage','Rankine Power Conversion System'),
                 ('Rankine Power Conversion System','Electrical Systems'),
                 ('Electrical Systems','Civils/Misc')]

#Create an interface and associate systems
for j,pair in enumerate(interface_pairs):
    interface = Interface(name='top_level_'+str(j))
    this_system = session.query(System).filter_by(name=pair[0]).first()
    interface.systems.append(this_system)
    this_system2 = session.query(System).filter_by(name=pair[1]).first()
    interface.systems.append(this_system2)
    session.add(interface)
    session.commit()
    
interface = Interface(name='RB2')
this_system = session.query(System).filter_by(name='Reactor Building Structure').first()
interface.systems.append(this_system)
this_system2 = session.query(System).filter_by(name='Reactor Building Vents & Drain').first()
interface.systems.append(this_system2)
session.add(interface)

#TODO! Create an enum of things that get passed to the interface, these could be mass, dimensions, temperature, power
#Need a scheme by which TES acts as the buffer. 


#TODO! Create a scheme by which requirements get propagated in standardized systems. E.g. if a requirement is present in
#one system and not another



session.commit()

session.close()


# -*- coding: utf-8 -*-
"""can change parameters then call in the contract type using one of the following functions:
    - for fixed price use: fixed_price
    - for cost+ use: cost_plus
    - for IPD use: ipd
"""

#import functionsfile as ff
import csv
import os
import numpy as np


#parameters
discount_rate = 0.05
design_cost = 10000
build_cost = 35000

"""need to work in target vs actual build cost"""

design_time = 4
build_time = 6
commission_time = 1
operating_time = 60

OM_per_year = 1000
revenue_per_year = 5500

actual_design_time = 4
actual_build_time = 6

"""def fixed_price(params):

params = {
    "discount_rate": discount_rate,
    "design_cost": design_cost,
    "build_cost": build_cost,
    "design_time": design_time,
    "build_time": build_time,
    "operating_time": operating_time,
    "OM_per_year": OM_per_year,
    "revenue_per_year": revenue_per_year,
    "actual_design_time": actual_design_time,
    "actual_build_time": actual_build_time,
    }

ff.fixed_price(params)"""


fp_design_payout_milestone = True #if set to true, utility pays cost of design when design is complete

actors=["vendor","utility","AE","constructor"]

#can edit stake in portions
percent_design = {"vendor":0.25,"utility":0,"AE":0.75,"constructor":0}
percent_build = {"vendor":0.15,"utility":0,"AE":0.25,"constructor":0.6}
percent_OM_to = {"vendor":0,"utility":1,"AE":0,"constructor":0}
percent_revenue_to = {"vendor":0,"utility":1,"AE":0,"constructor":0}

profit_margin = 0.1
contingency = 0.1
#inflation = TBD

"""work this into the inputs file as a target and actual progress arrays"""
target_design_progress=np.zeros(design_time)
target_design_progress[1]=50
target_design_progress[2]=75
target_design_progress[3]=100
target_build_progress=np.zeros(design_time + build_time)
target_build_progress[-1]=100
actual_design_progress=np.zeros(actual_design_time)
actual_design_progress[1]=50
actual_design_progress[2]=75
actual_design_progress[3]=100
actual_build_progress=np.zeros(actual_design_time + actual_build_time)
#actual_build_progress[-2]=50
actual_build_progress[-1]=100


#enter run name each time!!
run_name = input("Test Run")

from functionsfile import PDSystems

#run
#ff.fixed_price()
#ff.cost_plus()
#ff.ipd()

filename = "cost_risk_runs_bl.csv"
file_exists = os.path.isfile(filename)

contracts = ['fixed_price','cost_plus','ipd']

rows = []

for contract in contracts:
    #instantiate
    pds = PDSystems(operating_time,design_time,build_time,commission_time...) #TODO: all variables

    # run the contract model
    getattr(pds,contract)()

    # store outputs
    rows.append([
        run_name,
        contract_name,
        design_cost,
        build_cost,
        discount_rate,
        ff.NPV["vendor"],
        ff.NPV["utility"],
        ff.NPV["AE"],
        ff.NPV["constructor"]
    ])


with open(filename, 'w', newline='') as f:

    writer = csv.writer(f)

    if not file_exists:
        writer.writerow([
            "Run Name",
            "Contract Type",
            "Design Cost",
            "Build Cost",
            "Discount Rate",
            "Vendor NPV",
            "Utility NPV",
            "AE NPV",
            "Constructor NPV"
        ])

    writer.writerows(rows)



"""other option
with open(filename, 'a', newline='') as f:
    writer = csv.writer(f)

    if not file_exists:
        writer.writerow([
            "Run Name",
            "Vendor NPV",
            "Utility NPV",
            "AE NPV",
            "Constructor NPV"
        ])

    writer.writerow([
        run_name,
        ff.NPV["vendor"],
        ff.NPV["utility"],
        ff.NPV["AE"],
        ff.NPV["constructor"]
    ])
"""
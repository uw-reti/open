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

"""
#parameters
discount_rate = 0.05
design_cost = 10000
build_cost = 35000

#need to work in target vs actual build cost

design_time = 4
build_time = 6
commission_time = 1
operating_time = 60

OM_per_year = 1000
revenue_per_year = 5500

actual_design_time = 4
actual_build_time = 6


def fixed_price(params):

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


"""fp_design_payout_milestone = True #if set to true, utility pays cost of design when design is complete

actors=["vendor","utility","AE","constructor"]

#can edit stake in portions
percent_design = {"vendor":0.25,"utility":0,"AE":0.75,"constructor":0}
percent_build = {"vendor":0.15,"utility":0,"AE":0.25,"constructor":0.6}
percent_OM_to = {"vendor":0,"utility":1,"AE":0,"constructor":0}
percent_revenue_to = {"vendor":0,"utility":1,"AE":0,"constructor":0}

profit_margin = 0.1
contingency = 0.1
#inflation = TBD

#work this into the inputs file as a target and actual progress arrays
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
"""




# the part that runs it


from functionsfile import PDSystems

import sys
from pathlib import Path

import pandas as pd

actors = ("vendor", "AE", "constructor", "utility")
pds = ("fixed_price", "cost_plus", "ipd")


def row_to_inputs(row):
    if len(row) < 30:
        raise ValueError("Each row needs 30 columns")

    actual_design = [float(x) for x in row.iloc[10].split(",")]
    actual_build = [float(x) for x in row.iloc[11].split(",")]
    target_design = [float(x) for x in row.iloc[12].split(",")]
    target_build = [float(x) for x in row.iloc[13].split(",")]

    f = float
    i = lambda j: int(float(row.iloc[j]))

    return {
        "name": str(row.iloc[0]).strip(),
        "operating_time": i(1),
        "commission_time": i(2),
        "design_cost": f(row.iloc[3]),
        "build_cost": f(row.iloc[4]),
        "om_per_year": f(row.iloc[5]),
        "revenue_per_year": f(row.iloc[6]),
        "discount_rate": f(row.iloc[7]),
        "contingency": f(row.iloc[8]),
        "profit_margin": f(row.iloc[9]),
        "actual_design_progress": actual_design,
        "actual_build_progress": actual_build,
        "target_design_progress": target_design,
        "target_build_progress": target_build,
        "percent_design": {
            "vendor": f(row.iloc[14]),
            "AE": f(row.iloc[15]),
            "constructor": f(row.iloc[16]),
            "utility": f(row.iloc[17]),
        },
        "percent_build": {
            "vendor": f(row.iloc[18]),
            "AE": f(row.iloc[19]),
            "constructor": f(row.iloc[20]),
            "utility": f(row.iloc[21]),
        },
        "percent_OM_to": {
            "vendor": f(row.iloc[22]),
            "AE": f(row.iloc[23]),
            "constructor": f(row.iloc[24]),
            "utility": f(row.iloc[25]),
        },
        "percent_revenue_to": {
            "vendor": f(row.iloc[26]),
            "AE": f(row.iloc[27]),
            "constructor": f(row.iloc[28]),
            "utility": f(row.iloc[29]),
        },
    }


def run_models(inputs):
    """runs all three and returns NPV per actor for each"""
    m = PDSystems(inputs)
    npvs = {}
    m.fixed_price()
    npvs["fixed_price"] = dict(m.NPV)
    m.cost_plus()
    npvs["cost_plus"] = dict(m.NPV)
    m.ipd()
    npvs["ipd"] = dict(m.NPV)
    return npvs


def main():
    #you have to input your file route here for now.. will update when I ask/figure out how to upload one
    input_csv = Path("test_inputs.csv")
    #input_csv = Path("cost_risk_inputs.csv")
    #input_csv = Path(r"C:\Users\Veronica\Downloads\bl_inputs.csv")
    output_csv = input_csv.with_name(input_csv.stem + "_results.csv")

    df = pd.read_csv(input_csv, dtype=str, keep_default_na=False)
    if df.shape[1] < 30:
        print(f"Error: run needs 30 columns, found {df.shape[1]}.")
        sys.exit(1)

    results = []
    for idx in range(len(df)):
        row = df.iloc[idx]
        record = row.to_dict()
        npvs = run_models(row_to_inputs(row))
        try:
            for model in pds:
                for actor in actors:
                    record[f"{model}_npv_{actor}"] = npvs[model][actor]
        except Exception as e:
            for model in pds:
                for actor in actors:
                    record[f"{model}_npv_{actor}"] = None
            record["error"] = str(e)
        results.append(record)

    pd.DataFrame(results).to_csv(output_csv, index=False)
    print(f"Wrote {len(results)} row(s) to {output_csv}")

if __name__ == "__main__":
    main()
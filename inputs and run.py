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


from functionsfile import PDSystems

import sys
from pathlib import Path

import pandas as pd

actors = ("vendor", "AE", "constructor", "utility")
pds = ("fixed_price", "cost_plus","ipd")


def row_to_inputs(row):
    if len(row) < 40:
        raise ValueError("Each row needs 40 columns")

    actual_design = [float(x) for x in row.iloc[14].split(",")]
    actual_build = [float(x) for x in row.iloc[15].split(",")]
    actual_ipd = [float(x) for x in row.iloc[16].split(",")]
    target_design = [float(x) for x in row.iloc[17].split(",")]
    target_build = [float(x) for x in row.iloc[18].split(",")]
    target_ipd = [float(x) for x in row.iloc[19].split(",")]

    f = float
    i = lambda j: int(float(row.iloc[j]))

    return {
        "name": str(row.iloc[0]).strip(),
        "operating_time": i(1),
        "commission_time": i(2),
        "target_design_cost": f(row.iloc[3]),
        "target_build_cost": f(row.iloc[4]),
        "target_ipd_cost": f(row.iloc[5]),
        "design_cost": f(row.iloc[6]),
        "build_cost": f(row.iloc[7]),
        "om_per_year": f(row.iloc[8]),
        "revenue_per_year": f(row.iloc[9]),
        "discount_rate": f(row.iloc[10]),
        "contingency": f(row.iloc[11]),
        "ipd_contingency": f(row.iloc[12]),
        "profit_margin": f(row.iloc[13]),
        "actual_design_progress": actual_design,
        "actual_build_progress": actual_build,
        "actual_ipd_progress": actual_ipd,
        "target_design_progress": target_design,
        "target_build_progress": target_build,
        "target_ipd_progress": target_ipd,
        "percent_design": {
            "vendor": f(row.iloc[20]),
            "AE": f(row.iloc[21]),
            "constructor": f(row.iloc[22]),
            "utility": f(row.iloc[23]),
        },
        "percent_build": {
            "vendor": f(row.iloc[24]),
            "AE": f(row.iloc[25]),
            "constructor": f(row.iloc[26]),
            "utility": f(row.iloc[27]),
        },
        "percent_ipd": {
            "vendor": f(row.iloc[28]),
            "AE": f(row.iloc[29]),
            "constructor": f(row.iloc[30]),
            "utility": f(row.iloc[31]),
        },
        "percent_OM_to": {
            "vendor": f(row.iloc[32]),
            "AE": f(row.iloc[33]),
            "constructor": f(row.iloc[34]),
            "utility": f(row.iloc[35]),
        },
        "percent_revenue_to": {
            "vendor": f(row.iloc[36]),
            "AE": f(row.iloc[37]),
            "constructor": f(row.iloc[38]),
            "utility": f(row.iloc[39]),
        },
        "percent_pool_to": {
            "vendor": f(row.iloc[40]),
            "AE": f(row.iloc[41]),
            "constructor": f(row.iloc[42]),
            "utility": f(row.iloc[43]),
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
    if df.shape[1] < 40:
        print(f"Error: run needs 40 columns, found {df.shape[1]}.")
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
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from functionsfile import PDSystems


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PDSystems NPV Model")

        self.entries = {}

        self.build_tabs()
        self.build_inputs_tab()

    # -------------------------
    # TABS
    # -------------------------
    def build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.inputs_tab = ttk.Frame(self.notebook)
        self.results_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.inputs_tab, text="Inputs")
        self.notebook.add(self.results_tab, text="Results")

    # -------------------------
    # INPUTS TAB
    # -------------------------
    def build_inputs_tab(self):

        main = tk.Frame(self.inputs_tab)
        main.pack(padx=10, pady=10, anchor="nw")

        # ---------------- CORE INPUTS ----------------
        core = tk.LabelFrame(main, text="Core Project Inputs")
        core.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        fields = [
            ("Run Name / Descriptor", "name"),
            ("Design Time (years)", "design_time"),
            ("Build Time (years)", "build_time"),
            ("Operating Time (years)", "operating_time"),
            ("Commission Time (years)", "commission_time"),
            ("Design Cost", "design_cost"),
            ("Build Cost", "build_cost"),
            ("Revenue per Year", "revenue_per_year"),
            ("O&M per Year", "om_per_year"),
            ("Discount Rate", "discount_rate"),
            ("Contingency", "contingency"),
            ("Profit Margin", "profit_margin"),
        ]

        for i, (label, key) in enumerate(fields):
            tk.Label(core, text=label).grid(row=i, column=0, sticky="w")
            entry = tk.Entry(core, width=20)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.entries[key] = entry

        # ---------------- PROGRESS ARRAYS ----------------
        progress = tk.LabelFrame(main, text="Progress Arrays")
        progress.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        arrays = [
            ("Actual Design Progress (%)", "actual_design_progress"),
            ("Actual Build Progress (%)", "actual_build_progress"),
            ("Target Design Progress (%)", "target_design_progress"),
            ("Target Build Progress (%)", "target_build_progress"),
        ]

        for i, (label, key) in enumerate(arrays):
            tk.Label(progress, text=label).grid(row=i, column=0, sticky="w")
            entry = tk.Entry(progress, width=40)
            entry.grid(row=i, column=1, padx=5)
            self.entries[key] = entry

        # ---------------- SHARES ----------------
        shares = tk.LabelFrame(main, text="Shares by Actor")
        shares.grid(row=2, column=0, sticky="w", padx=5, pady=5)

        actors = ["vendor", "AE", "constructor", "utility"]
        categories = ["design", "build", "om", "revenue"]

        self.share_entries = {}

        for c, cat in enumerate(categories):
            tk.Label(shares, text=cat.capitalize()).grid(row=0, column=c+1)

        for r, actor in enumerate(actors):
            tk.Label(shares, text=actor).grid(row=r+1, column=0)

            for c, cat in enumerate(categories):
                key = f"{cat}_{actor}"
                entry = tk.Entry(shares, width=8)
                entry.grid(row=r+1, column=c+1)
                self.share_entries[key] = entry

        # ---------------- BUTTONS ----------------
        btns = tk.Frame(main)
        btns.grid(row=3, column=0, pady=10)

        tk.Button(btns, text="Load CSV", command=self.load_csv).pack(side="left", padx=5)
        tk.Button(btns, text="Run Model", command=self.run_model).pack(side="left", padx=5)
        tk.Button(btns, text="Export CSV", command=self.export_csv).pack(side="left", padx=5)

    # -------------------------
    # HELPERS
    # -------------------------
    def parse_array(self, text):
        return [float(x.strip()) for x in text.split(",") if x.strip()]

    @staticmethod
    def _read_inputs_csv(path):
        """First line is a header row. Each data row is mapped by column position (iloc 0..31)."""
        df = pd.read_csv(path, header=0)
        return df.dropna(how="all")

    def _inputs_from_csv_row(self, row):
        """Build PDSystems inputs dict from one CSV row (positional columns)."""
        return {
            "name": row.iloc[0],
            "operating_time": int(row.iloc[1]),
            "design_time": int(row.iloc[2]),
            "build_time": int(row.iloc[3]),
            "commission_time": int(row.iloc[4]),
            "design_cost": float(row.iloc[5]),
            "build_cost": float(row.iloc[6]),
            "om_per_year": float(row.iloc[7]),
            "revenue_per_year": float(row.iloc[8]),
            "discount_rate": float(row.iloc[9]),
            "contingency": float(row.iloc[10]),
            "profit_margin": float(row.iloc[11]),
            "actual_design_progress": [
                float(x.strip())
                for x in str(row.iloc[12]).split(",")
                if x.strip()
            ],
            "actual_build_progress": [
                float(x.strip())
                for x in str(row.iloc[13]).split(",")
                if x.strip()
            ],
            "target_design_progress": [
                float(x.strip())
                for x in str(row.iloc[14]).split(",")
                if x.strip()
            ],
            "target_build_progress": [
                float(x.strip())
                for x in str(row.iloc[15]).split(",")
                if x.strip()
            ],
            "design_shares": {
                "vendor": float(row.iloc[16]),
                "AE": float(row.iloc[17]),
                "constructor": float(row.iloc[18]),
                "utility": float(row.iloc[19]),
            },
            "build_shares": {
                "vendor": float(row.iloc[20]),
                "AE": float(row.iloc[21]),
                "constructor": float(row.iloc[22]),
                "utility": float(row.iloc[23]),
            },
            "om_shares": {
                "vendor": float(row.iloc[24]),
                "AE": float(row.iloc[25]),
                "constructor": float(row.iloc[26]),
                "utility": float(row.iloc[27]),
            },
            "revenue_shares": {
                "vendor": float(row.iloc[28]),
                "AE": float(row.iloc[29]),
                "constructor": float(row.iloc[30]),
                "utility": float(row.iloc[31]),
            },
        }

    def collect_inputs(self):
        data = {}

        for key, entry in self.entries.items():
            val = entry.get()

            if "progress" in key:
                data[key] = self.parse_array(val)
            else:
                try:
                    data[key] = float(val)
                except:
                    data[key] = val

        actors = ["vendor", "AE", "constructor", "utility"]

        data["design_shares"] = {}
        data["build_shares"] = {}
        data["om_shares"] = {}
        data["revenue_shares"] = {}

        for actor in actors:
            data["design_shares"][actor] = float(self.share_entries[f"design_{actor}"].get() or 0)
            data["build_shares"][actor] = float(self.share_entries[f"build_{actor}"].get() or 0)
            data["om_shares"][actor] = float(self.share_entries[f"om_{actor}"].get() or 0)
            data["revenue_shares"][actor] = float(self.share_entries[f"revenue_{actor}"].get() or 0)

        return data

    # -------------------------
    # ACTIONS
    # -------------------------
    def run_model(self):

        inputs = self.collect_inputs()
        model = PDSystems(inputs)

        model.fixed_price()
        fp_npv = dict(model.NPV)
        fp_total = sum(fp_npv.values())

        model.cost_plus()
        cp_npv = dict(model.NPV)
        cp_total = sum(cp_npv.values())

        model.ipd()
        ipd_npv = dict(model.NPV)
        ipd_total = sum(ipd_npv.values())

        self.results = {
            "fixed_price": fp_npv,
            "cost_plus": cp_npv,
            "ipd": ipd_npv,
        }
        self.results["_totals"] = {
            "fixed_price_NPV": fp_total,
            "cost_plus_NPV": cp_total,
            "IPD_NPV": ipd_total,
        }

        # show results
        for widget in self.results_tab.winfo_children():
            widget.destroy()

        tk.Label(
            self.results_tab,
            text=(
                f"Total NPV (all actors), fixed price: {fp_total:,.2f}\n"
                f"Total NPV (all actors), cost plus: {cp_total:,.2f}\n"
                f"Total NPV (all actors), IPD: {ipd_total:,.2f}"
            ),
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        for title, npv_dict in (
            ("Fixed price (per actor)", fp_npv),
            ("Cost plus (per actor)", cp_npv),
            ("IPD (per actor)", ipd_npv),
        ):
            tk.Label(
                self.results_tab,
                text=title,
                font=("TkDefaultFont", 9, "bold"),
            ).pack(anchor="w", pady=(6, 0))
            for k, v in npv_dict.items():
                tk.Label(self.results_tab, text=f"  {k}: {v:,.2f}").pack(anchor="w")

        self.notebook.select(self.results_tab)

    def load_csv(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV", "*.csv")]
        )

        if not path:
            return

        df = self._read_inputs_csv(path)
        self.loaded_df = df
        self.loaded_csv_path = path

        row = df.iloc[0]

        mapping = {
            "name": 0,                    # A
            "operating_time": 1,          # B
            "design_time": 2,             # C
            "build_time": 3,              # D
            "commission_time": 4,         # E
            "design_cost": 5,             # F
            "build_cost": 6,              # G
            "om_per_year": 7,             # H
            "revenue_per_year": 8,        # I
            "discount_rate": 9,           # J
            "contingency": 10,            # K
            "profit_margin": 11,          # L
            "actual_design_progress": 12, # M
            "actual_build_progress": 13,  # N
            "target_design_progress": 14, # O
            "target_build_progress": 15,  # P
        }

        for key, col_idx in mapping.items():

            value = row.iloc[col_idx]

            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, str(value))


        share_mapping = {
            # DESIGN
            "design_vendor": 16,       # Q
            "design_AE": 17,           # R
            "design_constructor": 18,  # S
            "design_utility": 19,      # T

            # BUILD
            "build_vendor": 20,        # U
            "build_AE": 21,            # V
            "build_constructor": 22,   # W
            "build_utility": 23,       # X

            # OM
            "om_vendor": 24,           # Y
            "om_AE": 25,               # Z
            "om_constructor": 26,      # AA
            "om_utility": 27,          # AB

            # REVENUE
            "revenue_vendor": 28,      # AC
            "revenue_AE": 29,          # AD
            "revenue_constructor": 30, # AE
            "revenue_utility": 31,     # AF
        }

        for key, col_idx in share_mapping.items():

            value = row.iloc[col_idx]

            if key in self.share_entries:
                self.share_entries[key].delete(0, tk.END)
                self.share_entries[key].insert(0, str(value))

        n = len(df)
        messagebox.showinfo(
            "CSV loaded",
            f"Loaded {n} data row(s) below the header. The form shows the first data row.\n"
            "Use Export CSV to run every data row and append all three NPV totals.",
        )

    def export_csv(self):

        if not hasattr(self, "loaded_df") or self.loaded_df is None or len(self.loaded_df) == 0:
            path = filedialog.askopenfilename(
                title="Select input CSV (all rows will be run)",
                filetypes=[("CSV", "*.csv")],
            )
            if not path:
                return
            self.loaded_df = self._read_inputs_csv(path)
            self.loaded_csv_path = path

        df = self.loaded_df.copy()

        output_rows = []

        for row_idx, (_, row) in enumerate(df.iterrows()):

            try:
                inputs = self._inputs_from_csv_row(row)

                model = PDSystems(inputs)

                model.fixed_price()
                fixed_price_npv = sum(model.NPV.values())

                model.cost_plus()
                cost_plus_npv = sum(model.NPV.values())

                model.ipd()
                ipd_npv = sum(model.NPV.values())

                output_row = row.to_dict()
                output_row["csv_row_index"] = row_idx
                output_row["fixed_price_NPV"] = fixed_price_npv
                output_row["cost_plus_NPV"] = cost_plus_npv
                output_row["IPD_NPV"] = ipd_npv
                output_row["batch_error"] = ""

            except Exception as e:
                output_row = row.to_dict()
                output_row["csv_row_index"] = row_idx
                output_row["fixed_price_NPV"] = None
                output_row["cost_plus_NPV"] = None
                output_row["IPD_NPV"] = None
                output_row["batch_error"] = str(e)

            output_rows.append(output_row)

        output_df = pd.DataFrame(output_rows)

        base = os.path.basename(self.loaded_csv_path)
        initial = base.replace(".csv", "_results.csv", 1) if base.lower().endswith(".csv") else base + "_results.csv"

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=initial,
        )

        if save_path:
            output_df.to_csv(save_path, index=False)
            messagebox.showinfo(
                "Export complete",
                f"Wrote {len(output_df)} row(s) to:\n{save_path}",
            )
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
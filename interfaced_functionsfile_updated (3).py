import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import numpy as np
import pandas as pd

# Use ORIGINAL model (unchanged)
import functionsfile as fx


class PDSystemsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDSystems NPV Model")
        self.root.geometry("1200x820")

        self.actors = ["vendor", "AE", "constructor", "utility"]
        self.share_groups = [
            ("percent_design", "Design Share"),
            ("percent_build", "Build Share"),
            ("percent_OM_to", "O&M Share"),
            ("percent_revenue_to", "Revenue Share"),
        ]

        self.entries = {}
        self.share_entries = {}
        self.last_results = {}

        self.default_csv_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "pd_systems_results.csv",
        )

        self._build_ui()
        self._load_defaults()

    # ---------------- UI ----------------

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        input_frame = ttk.Frame(notebook)
        output_frame = ttk.Frame(notebook)
        notebook.add(input_frame, text="Inputs")
        notebook.add(output_frame, text="Results")

        self._build_input_tab(input_frame)
        self._build_output_tab(output_frame)

    def _build_input_tab(self, parent):
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        row = 0

        ttk.Label(scrollable, text="Core Project Inputs", font=("Segoe UI", 12, "bold")).grid(row=row, column=0, columnspan=4, sticky="w", pady=(10, 6))
        row += 1

        core_fields = [
            ("run_name", "Run Name / Descriptor"),
            ("operating_time", "Operating Time (years)"),
            ("design_time", "Design Time (years)"),
            ("build_time", "Build Time (years)"),
            ("commission_time", "Commission Time (years)"),
            ("design_cost", "Design Cost"),
            ("build_cost", "Build Cost"),
            ("OM_per_year", "O&M per Year"),
            ("revenue_per_year", "Revenue per Year"),
            ("discount_rate", "Discount Rate (decimal)"),
            ("contingency", "Contingency (decimal)"),
            ("profit_margin", "Profit Margin (decimal)"),
        ]

        for i, (key, label) in enumerate(core_fields):
            r = row + i // 2
            c = (i % 2) * 2
            ttk.Label(scrollable, text=label).grid(row=r, column=c, sticky="w", padx=6, pady=4)
            entry = ttk.Entry(scrollable, width=28)
            entry.grid(row=r, column=c + 1, sticky="ew", padx=6, pady=4)
            self.entries[key] = entry

        row += (len(core_fields) + 1) // 2

        ttk.Label(scrollable, text="Progress Arrays", font=("Segoe UI", 12, "bold")).grid(row=row, column=0, columnspan=4, sticky="w", pady=(18, 6))
        row += 1

        progress_fields = [
            ("actual_design_progress", "Actual Design Progress (%)"),
            ("actual_build_progress", "Actual Build Progress (%)"),
            ("target_design_progress", "Target Design Progress (%)"),
            ("target_build_progress", "Target Build Progress (%)"),
        ]

        for i, (key, label) in enumerate(progress_fields):
            ttk.Label(scrollable, text=label).grid(row=row + i, column=0, sticky="w", padx=6, pady=4)
            entry = ttk.Entry(scrollable, width=60)
            entry.grid(row=row + i, column=1, columnspan=3, sticky="ew", padx=6, pady=4)
            self.entries[key] = entry

        row += len(progress_fields)

        ttk.Label(scrollable, text="Shares by Actor", font=("Segoe UI", 12, "bold")).grid(row=row, column=0, columnspan=5, sticky="w", pady=(18, 6))
        row += 1

        ttk.Label(scrollable, text="Category").grid(row=row, column=0, sticky="w", padx=6)
        for j, actor in enumerate(self.actors, start=1):
            ttk.Label(scrollable, text=actor).grid(row=row, column=j, sticky="w", padx=6)
        row += 1

        for group_key, group_label in self.share_groups:
            ttk.Label(scrollable, text=group_label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
            self.share_entries[group_key] = {}
            for j, actor in enumerate(self.actors, start=1):
                entry = ttk.Entry(scrollable, width=12)
                entry.grid(row=row, column=j, sticky="ew", padx=6, pady=4)
                self.share_entries[group_key][actor] = entry
            row += 1

        ttk.Label(scrollable, text=f"Running CSV file: {os.path.basename(self.default_csv_path)}").grid(row=row, column=0, columnspan=4, sticky="w", padx=6, pady=(8, 10))
        row += 1

        button_frame = ttk.Frame(scrollable)
        button_frame.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(10, 20))

        ttk.Button(button_frame, text="Run Model", command=self.run_model).pack(side="left", padx=6)
        ttk.Button(button_frame, text="Append to Running CSV", command=self.export_csv).pack(side="left", padx=6)
        ttk.Button(button_frame, text="Run Batch CSV", command=self.run_batch_csv).pack(side="left", padx=6)

    def _build_output_tab(self, parent):
        ttk.Label(parent, text="Summary", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.summary_text = tk.Text(parent, height=12, wrap="word")
        self.summary_text.pack(fill="x", padx=10, pady=6)

        ttk.Label(parent, text="CSV Preview", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.preview_text = tk.Text(parent, wrap="none")
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ---------------- DEFAULTS ----------------

    def _load_defaults(self):
        defaults = {
            "run_name": "descriptor",
            "operating_time": "10",
            "design_time": "3",
            "build_time": "4",
            "commission_time": "1",
            "design_cost": "10000",
            "build_cost": "35000",
            "OM_per_year": "100",
            "revenue_per_year": "1200",
            "discount_rate": "0.05",
            "contingency": "0.10",
            "profit_margin": "0.15",
            "actual_design_progress": "20,60,100",
            "actual_build_progress": "10,30,60,100",
            "target_design_progress": "40,80,100",
            "target_build_progress": "25,50,75,100",
        }

        for key, value in defaults.items():
            self.entries[key].insert(0, value)

        share_defaults = {
            "percent_design": {"vendor": "0.20", "AE": "0.60", "constructor": "0.10", "utility": "0.10"},
            "percent_build": {"vendor": "0.30", "AE": "0.10", "constructor": "0.50", "utility": "0.10"},
            "percent_OM_to": {"vendor": "0.00", "AE": "0.00", "constructor": "0.00", "utility": "1.00"},
            "percent_revenue_to": {"vendor": "0.00", "AE": "0.00", "constructor": "0.00", "utility": "1.00"},
        }

        for group, actors in share_defaults.items():
            for actor, value in actors.items():
                self.share_entries[group][actor].insert(0, value)

    # ---------------- HELPERS ----------------

    def _parse_float(self, key):
        return float(self.entries[key].get().strip())

    def _parse_int(self, key):
        return int(float(self.entries[key].get().strip()))

    def _parse_progress_list(self, text):
        text = text.strip()
        if not text:
            return []
        return [float(p.strip()) for p in text.replace(";", ",").split(",") if p.strip()]

    def _get_inputs(self):
        data = {
            "run_name": self.entries["run_name"].get().strip() or "descriptor",
            "operating_time": self._parse_int("operating_time"),
            "design_time": self._parse_int("design_time"),
            "build_time": self._parse_int("build_time"),
            "commission_time": self._parse_int("commission_time"),
            "design_cost": self._parse_float("design_cost"),
            "build_cost": self._parse_float("build_cost"),
            "OM_per_year": self._parse_float("OM_per_year"),
            "revenue_per_year": self._parse_float("revenue_per_year"),
            "discount_rate": self._parse_float("discount_rate"),
            "contingency": self._parse_float("contingency"),
            "profit_margin": self._parse_float("profit_margin"),
            "actual_design_progress": self._parse_progress_list(self.entries["actual_design_progress"].get()),
            "actual_build_progress": self._parse_progress_list(self.entries["actual_build_progress"].get()),
            "target_design_progress": self._parse_progress_list(self.entries["target_design_progress"].get()),
            "target_build_progress": self._parse_progress_list(self.entries["target_build_progress"].get()),
            "actors": self.actors,
        }

        for group_key, _ in self.share_groups:
            data[group_key] = {
                actor: float(self.share_entries[group_key][actor].get().strip())
                for actor in self.actors
            }

        return data

    """
    def _inject_inputs_to_model(self, inputs):
        for k, v in inputs.items():
            if "progress" in k and isinstance(v, list):
                v = np.array(v)
            setattr(fx, k, v)
    """

    # ---------------- RUN SINGLE ----------------

    def run_model(self):
        try:
            inputs = self._get_inputs()
            run_name = inputs.pop("run_name")

            #self._inject_inputs_to_model(inputs)

            model = fx.PDSystems(**inputs)

            results = {
                "Fixed Price": model.fixed_price(),
                "Cost Plus": model.cost_plus(),
                "IPD": model.ipd(),
            }

            self.last_results = {"run_name": run_name, "results": results}
            self._show_results(results)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------------- BATCH CSV ----------------

    def run_batch_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return

        df = pd.read_csv(path)
        results = []

        for _, row in df.iterrows():

            inputs = row.to_dict()

            # Convert progress strings → lists
            for k, v in inputs.items():
                if "progress" in k and isinstance(v, str):
                    inputs[k] = [float(x) for x in v.replace(";", ",").split(",")]

            model = fx.PDSystems(**inputs)

            fp = model.fixed_price()
            cp = model.cost_plus()
            ipd = model.ipd()

            # Flatten NPV results into columns
            results.append({
                "fp_vendor": fp["NPV"].get("vendor", 0),
                "fp_AE": fp["NPV"].get("AE", 0),
                "fp_constructor": fp["NPV"].get("constructor", 0),
                "fp_utility": fp["NPV"].get("utility", 0),

                "cp_vendor": cp["NPV"].get("vendor", 0),
                "cp_AE": cp["NPV"].get("AE", 0),
                "cp_constructor": cp["NPV"].get("constructor", 0),
                "cp_utility": cp["NPV"].get("utility", 0),

                "ipd_vendor": ipd["NPV"].get("vendor", 0),
                "ipd_AE": ipd["NPV"].get("AE", 0),
                "ipd_constructor": ipd["NPV"].get("constructor", 0),
                "ipd_utility": ipd["NPV"].get("utility", 0),
            })

        results_df = pd.DataFrame(results)

        output = pd.concat([df, results_df], axis=1)

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile="batch_results.csv"
        )

        if not save_path:
            save_path = os.path.join(os.getcwd(), "batch_results.csv")

        output.to_csv(save_path, index=False)

        messagebox.showinfo("Saved", f"Results saved to:\n{save_path}")


    # ---------------- OUTPUT ----------------

    def _show_results(self, results):
        self.summary_text.delete("1.0", tk.END)
        lines = []
        for name, res in results.items():
            lines.append(name)
            lines.append("-" * len(name))
            if isinstance(res, dict) and "NPV" in res:
                for actor, val in res["NPV"].items():
                    lines.append(f"{actor}: {val:,.2f}")
            lines.append("")
        self.summary_text.insert("1.0", "\n".join(lines))

    def export_csv(self):
        if not self.last_results:
            messagebox.showwarning("No Results", "Run the model first.")
            return

        rows = []
        run_name = self.last_results["run_name"]
        for model_name, result in self.last_results["results"].items():
            row = {"run name": run_name, "contract": model_name}
            if isinstance(result, dict) and "NPV" in result:
                for actor, val in result["NPV"].items():
                    row[f"{actor} NPV"] = val
            rows.append(row)

        file_exists = os.path.exists(self.default_csv_path)
        with open(self.default_csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            if not file_exists:
                writer.writeheader()
            writer.writerows(rows)

        messagebox.showinfo("Export", "Results appended to CSV")


if __name__ == "__main__":
    root = tk.Tk()
    app = PDSystemsGUI(root)
    root.mainloop()

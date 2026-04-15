import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np

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
        ttk.Label(
            scrollable,
            text="Core Project Inputs",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=row, column=0, columnspan=4, sticky="w", pady=(10, 6))
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
            ttk.Label(scrollable, text=label).grid(
                row=r, column=c, sticky="w", padx=6, pady=4
            )
            entry = ttk.Entry(scrollable, width=28)
            entry.grid(row=r, column=c + 1, sticky="ew", padx=6, pady=4)
            self.entries[key] = entry

        row += (len(core_fields) + 1) // 2

        ttk.Label(
            scrollable,
            text="Progress Arrays",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=row, column=0, columnspan=4, sticky="w", pady=(18, 6))
        row += 1

        progress_fields = [
            ("actual_design_progress", "Actual Design Progress (%)"),
            ("actual_build_progress", "Actual Build Progress (%)"),
            ("target_design_progress", "Target Design Progress (%)"),
            ("target_build_progress", "Target Build Progress (%)"),
        ]

        for i, (key, label) in enumerate(progress_fields):
            ttk.Label(scrollable, text=label).grid(
                row=row + i, column=0, sticky="w", padx=6, pady=4
            )
            entry = ttk.Entry(scrollable, width=60)
            entry.grid(
                row=row + i,
                column=1,
                columnspan=3,
                sticky="ew",
                padx=6,
                pady=4,
            )
            self.entries[key] = entry

        row += len(progress_fields)

        ttk.Label(
            scrollable,
            text="Shares by Actor",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=row, column=0, columnspan=5, sticky="w", pady=(18, 6))
        row += 1

        ttk.Label(scrollable, text="Category").grid(
            row=row, column=0, sticky="w", padx=6
        )
        for j, actor in enumerate(self.actors, start=1):
            ttk.Label(scrollable, text=actor).grid(
                row=row, column=j, sticky="w", padx=6
            )
        row += 1

        for group_key, group_label in self.share_groups:
            ttk.Label(scrollable, text=group_label).grid(
                row=row, column=0, sticky="w", padx=6, pady=4
            )
            self.share_entries[group_key] = {}
            for j, actor in enumerate(self.actors, start=1):
                entry = ttk.Entry(scrollable, width=12)
                entry.grid(row=row, column=j, sticky="ew", padx=6, pady=4)
                self.share_entries[group_key][actor] = entry
            row += 1

        ttk.Label(
            scrollable,
            text=f"Running CSV file: {os.path.basename(self.default_csv_path)}",
        ).grid(row=row, column=0, columnspan=4, sticky="w", padx=6, pady=(8, 10))
        row += 1

        button_frame = ttk.Frame(scrollable)
        button_frame.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(10, 20))

        ttk.Button(
            button_frame,
            text="Run Model",
            command=self.run_model,
        ).pack(side="left", padx=6, pady=4)

        ttk.Button(
            button_frame,
            text="Append to Running CSV",
            command=self.export_csv,
        ).pack(side="left", padx=6, pady=4)

        ttk.Button(
            button_frame,
            text="Upload and Run Batch CSV",
            command=self.run_batch_mode,
        ).pack(side="left", padx=6, pady=4)

    def _build_output_tab(self, parent):
        ttk.Label(
            parent,
            text="Summary",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", padx=10, pady=(10, 6))

        self.summary_text = tk.Text(parent, height=12, wrap="word")
        self.summary_text.pack(fill="x", padx=10, pady=6)

        ttk.Label(
            parent,
            text="CSV Preview",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", padx=10, pady=(10, 6))

        self.preview_text = tk.Text(parent, wrap="none")
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

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
            "percent_design": {
                "vendor": "0.20",
                "AE": "0.60",
                "constructor": "0.10",
                "utility": "0.10",
            },
            "percent_build": {
                "vendor": "0.30",
                "AE": "0.10",
                "constructor": "0.50",
                "utility": "0.10",
            },
            "percent_OM_to": {
                "vendor": "0.00",
                "AE": "0.00",
                "constructor": "0.00",
                "utility": "1.00",
            },
            "percent_revenue_to": {
                "vendor": "0.00",
                "AE": "0.00",
                "constructor": "0.00",
                "utility": "1.00",
            },
        }

        for group, actors in share_defaults.items():
            for actor, value in actors.items():
                self.share_entries[group][actor].insert(0, value)

    def _parse_float(self, key):
        return float(self.entries[key].get().strip())

    def _parse_int(self, key):
        return int(float(self.entries[key].get().strip()))

    def _parse_progress_list(self, text):
        text = text.strip()
        if not text:
            return []
        parts = [p.strip() for p in text.replace(";", ",").split(",") if p.strip()]
        return [float(p) for p in parts]

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
            "actual_design_progress": self._parse_progress_list(
                self.entries["actual_design_progress"].get()
            ),
            "actual_build_progress": self._parse_progress_list(
                self.entries["actual_build_progress"].get()
            ),
            "target_design_progress": self._parse_progress_list(
                self.entries["target_design_progress"].get()
            ),
            "target_build_progress": self._parse_progress_list(
                self.entries["target_build_progress"].get()
            ),
            "actors": self.actors,
        }

        for group_key, _ in self.share_groups:
            data[group_key] = {
                actor: float(self.share_entries[group_key][actor].get().strip())
                for actor in self.actors
            }

        return data

    def _validate_inputs(self, inputs):
        if not inputs["actual_design_progress"]:
            raise ValueError("Actual design progress cannot be blank.")
        if not inputs["actual_build_progress"]:
            raise ValueError("Actual build progress cannot be blank.")

        for name in [
            "actual_design_progress",
            "actual_build_progress",
            "target_design_progress",
            "target_build_progress",
        ]:
            arr = inputs[name]
            if not arr:
                continue
            for x in arr:
                if x < 0 or x > 100:
                    raise ValueError(f"{name} values must be between 0 and 100.")
            if any(arr[i] < arr[i - 1] for i in range(1, len(arr))):
                raise ValueError(f"{name} must be cumulative and non-decreasing.")

    def run_model(self):
        try:
            inputs = self._get_inputs()
            self._validate_inputs(inputs)

            model_inputs = dict(inputs)
            run_name = model_inputs.pop("run_name")

            fx.PDSystems(**model_inputs)

            self.last_results = {
                "run_name": run_name,
                "results": {
                    "Fixed Price": model.fixed_price(),
                    "Cost Plus": model.cost_plus(),
                    "IPD": model.ipd(),
                },
            }

            self._show_results(self.last_results["results"])

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run_batch_mode(self):
        from tkinter import filedialog

        input_path = filedialog.askopenfilename(
            title="Select Input CSV",
            filetypes=[("CSV Files", "*.csv")]
        )

        if not input_path:
            return

        output_path = input_path.replace(".csv", "_output.csv")

        try:
            run_batch_csv(input_path, output_path)
            messagebox.showinfo("Success", f"Batch run complete:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _results_to_summary_rows(self):
        if not self.last_results:
            return []

        run_name = self.last_results["run_name"]
        results = self.last_results["results"]

        design_cost = self._parse_float("design_cost")
        build_cost = self._parse_float("build_cost")
        discount_rate = self._parse_float("discount_rate")

        contract_name_map = {
            "Fixed Price": "fixed price",
            "Cost Plus": "cost+",
            "IPD": "ipd",
        }

        rows = []
        for model_name, result in results.items():
            rows.append(
                {
                    "run name": run_name,
                    "contract type": contract_name_map.get(
                        model_name, model_name.lower()
                    ),
                    "design cost": design_cost,
                    "build cost": build_cost,
                    "discount rate": discount_rate,
                    "vendor NPV": float(result["NPV"].get("vendor", 0.0)),
                    "AE NPV": float(result["NPV"].get("AE", 0.0)),
                    "constructor NPV": float(result["NPV"].get("constructor", 0.0)),
                    "utility NPV": float(result["NPV"].get("utility", 0.0)),
                }
            )
        return rows

    def _show_results(self, results):
        self.summary_text.delete("1.0", tk.END)

        lines = []
        for model_name, result in results.items():
            lines.append(model_name)
            lines.append("-" * len(model_name))
            for actor, value in result["NPV"].items():
                lines.append(f"{actor}: {value:,.2f}")
            lines.append("")

        self.summary_text.insert("1.0", "\n".join(lines))

        preview_rows = self._results_to_summary_rows()
        self.preview_text.delete("1.0", tk.END)

        if preview_rows:
            headers = list(preview_rows[0].keys())
            preview_lines = [",".join(headers)]
            for row in preview_rows:
                preview_lines.append(",".join(str(row[h]) for h in headers))
            self.preview_text.insert("1.0", "\n".join(preview_lines))

    def export_csv(self):
        if not self.last_results:
            messagebox.showwarning("No Results", "Run the model first.")
            return

        try:
            rows = self._results_to_summary_rows()
            if not rows:
                raise ValueError("No result rows available to export.")

            file_exists = os.path.exists(self.default_csv_path)
            write_header = not (file_exists and os.path.getsize(self.default_csv_path) > 0)

            with open(self.default_csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                if write_header:
                    writer.writeheader()
                writer.writerows(rows)

            if write_header:
                messagebox.showinfo(
                    "Export Complete",
                    f"Created running CSV:\n{self.default_csv_path}",
                )
            else:
                messagebox.showinfo(
                    "Export Complete",
                    f"Appended results to:\n{self.default_csv_path}",
                )

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

def run_batch_csv(input_csv_path, output_csv_path):
    import csv

    def parse_list(s):
        if not s:
            return []
        return [float(x.strip()) for x in s.split(",") if x.strip()]

    results = []

    with open(input_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                inputs = {
                    "operating_time": int(row["operating_time"]),
                    "design_time": int(row["design_time"]),
                    "build_time": int(row["build_time"]),
                    "commission_time": int(row["commission_time"]),
                    "design_cost": float(row["design_cost"]),
                    "build_cost": float(row["build_cost"]),
                    "OM_per_year": float(row["OM_per_year"]),
                    "revenue_per_year": float(row["revenue_per_year"]),
                    "discount_rate": float(row["discount_rate"]),
                    "contingency": float(row["contingency"]),
                    "profit_margin": float(row["profit_margin"]),
                    "actual_design_progress": parse_list(row["actual_design_progress"]),
                    "actual_build_progress": parse_list(row["actual_build_progress"]),
                    "target_design_progress": parse_list(row.get("target_design_progress", "")),
                    "target_build_progress": parse_list(row.get("target_build_progress", "")),
                    "actors": ["vendor", "AE", "constructor", "utility"],
                }

                inputs["percent_design"] = {
                    "vendor": float(row["vendor_design"]),
                    "AE": float(row["AE_design"]),
                    "constructor": float(row["constructor_design"]),
                    "utility": float(row["utility_design"]),
                }

                inputs["percent_build"] = {
                    "vendor": float(row["vendor_build"]),
                    "AE": float(row["AE_build"]),
                    "constructor": float(row["constructor_build"]),
                    "utility": float(row["utility_build"]),
                }

                inputs["percent_OM_to"] = {
                    "vendor": float(row["vendor_om"]),
                    "AE": float(row["AE_om"]),
                    "constructor": float(row["constructor_om"]),
                    "utility": float(row["utility_om"]),
                }

                inputs["percent_revenue_to"] = {
                    "vendor": float(row["vendor_rev"]),
                    "AE": float(row["AE_rev"]),
                    "constructor": float(row["constructor_rev"]),
                    "utility": float(row["utility_rev"]),
                }

                model = fx.PDSystems(**inputs)

                outputs = {
                    "fixed_vendor_NPV": model.fixed_price()["NPV"]["vendor"],
                    "fixed_AE_NPV": model.fixed_price()["NPV"]["AE"],
                    "fixed_constructor_NPV": model.fixed_price()["NPV"]["constructor"],
                    "fixed_utility_NPV": model.fixed_price()["NPV"]["utility"],

                    "costplus_vendor_NPV": model.cost_plus()["NPV"]["vendor"],
                    "costplus_AE_NPV": model.cost_plus()["NPV"]["AE"],
                    "costplus_constructor_NPV": model.cost_plus()["NPV"]["constructor"],
                    "costplus_utility_NPV": model.cost_plus()["NPV"]["utility"],

                    "ipd_vendor_NPV": model.ipd()["NPV"]["vendor"],
                    "ipd_AE_NPV": model.ipd()["NPV"]["AE"],
                    "ipd_constructor_NPV": model.ipd()["NPV"]["constructor"],
                    "ipd_utility_NPV": model.ipd()["NPV"]["utility"],
                }

                results.append({**row, **outputs})

            except Exception as e:
                results.append({**row, "error": str(e)})

    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

if __name__ == "__main__":
    root = tk.Tk()
    app = PDSystemsGUI(root)
    root.mainloop()
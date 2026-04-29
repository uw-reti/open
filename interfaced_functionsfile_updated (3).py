import tkinter as tk
from tkinter import ttk, filedialog
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
            data["design_shares"][actor] = float(self.share_entries[f"design_{actor}"].get())
            data["build_shares"][actor] = float(self.share_entries[f"build_{actor}"].get())
            data["om_shares"][actor] = float(self.share_entries[f"om_{actor}"].get())
            data["revenue_shares"][actor] = float(self.share_entries[f"revenue_{actor}"].get())

        return data

    # -------------------------
    # ACTIONS
    # -------------------------
    def run_model(self):
        inputs = self.collect_inputs()
        model = PDSystems(inputs)

        self.results = model.run_model()

        # show results
        for widget in self.results_tab.winfo_children():
            widget.destroy()

        for i, (k, v) in enumerate(self.results.items()):
            tk.Label(self.results_tab, text=f"{k}: {v:.2f}").pack(anchor="w")

        self.notebook.select(self.results_tab)

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return

        df = pd.read_csv(path)

        for key in self.entries:
            if key in df.columns:
                self.entries[key].delete(0, tk.END)
                self.entries[key].insert(0, str(df[key].iloc[0]))

    def export_csv(self):
        if not hasattr(self, "results"):
            return

        df = pd.DataFrame([self.results])

        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if path:
            df.to_csv(path, index=False)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
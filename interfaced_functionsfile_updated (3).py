import os
import re
import sys
from pathlib import Path

# If the IDE "Run" button uses a global Python without your deps, re-run using this folder's .venv.
_root = Path(__file__).resolve().parent
_script = Path(__file__).resolve()
_venv_python = _root / ".venv" / "Scripts" / "python.exe"
if _venv_python.is_file():
    try:
        _wrong_interpreter = Path(sys.executable).resolve() != _venv_python.resolve()
    except OSError:
        _wrong_interpreter = True
    if _wrong_interpreter:
        import subprocess

        rc = subprocess.call([str(_venv_python), str(_script), *sys.argv[1:]])
        raise SystemExit(rc)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from functionsfile import PDSystems


class App:
    """PDSystems NPV GUI.

    **cost_risk_inputs** CSV (main batch format): first 32 columns A–AF — A–L core scalars;
    M–N comma-separated actual design / build cumulative %; O–P target design / build %;
    Q–AF sixteen share fractions in order: design (vendor, AE, constructor, utility), then build,
    then O&M, then revenue (same actor order in each block). Headers are matched case-insensitively;
    if headers are missing but 32+ columns exist, the same layout is read by column position.
    """

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


    def parse_array(self, text):
        return [float(x.strip()) for x in text.split(",") if x.strip()]

    @staticmethod
    def _norm_header(s):
        """Normalize CSV header for matching: lower, strip, collapse spaces/hyphens to underscores."""
        t = str(s).strip().lower()
        return re.sub(r"[\s\-]+", "_", t)

    @staticmethod
    def _header_lookup(df):
        """Map normalized header -> first physical column name in the file."""
        m = {}
        for c in df.columns:
            k = App._norm_header(c)
            if k and k not in m:
                m[k] = c
        return m

    def _cell_raw(self, row, lookup, *aliases):
        """Return stripped string cell for first alias that matches a column (case/spacing insensitive)."""
        for a in aliases:
            col = lookup.get(self._norm_header(a))
            if col is None or col not in row.index:
                continue
            v = row[col]
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return ""
            return str(v).strip()
        return ""

    def _cell_req_float(self, row, lookup, row_num, *aliases, label=None):
        s = self._cell_raw(row, lookup, *aliases)
        if s == "":
            lab = label or aliases[0]
            raise ValueError(f"Row {row_num}: missing or empty column for {lab!r} (tried {list(aliases)}).")
        return float(s)

    def _cell_req_int(self, row, lookup, row_num, *aliases, label=None):
        return int(float(self._cell_req_float(row, lookup, row_num, *aliases, label=label)))

    @staticmethod
    def _parse_progress_cell(text):
        if text is None or (isinstance(text, float) and pd.isna(text)):
            return []
        s = str(text).strip().replace(";", ",")
        if not s:
            return []
        return [float(x.strip()) for x in s.split(",") if x.strip()]

    @staticmethod
    def _read_inputs_csv(path):
        """Read **cost_risk_inputs** CSV: row 1 = headers, then one project per row.

        Expected layout (first 32 columns A–AF): A–L core inputs; M–N actual design/build progress
        (comma-separated %); O–P target design/build progress; Q–T design shares; U–X build;
        Y–AB O&M; AC–AF revenue — each share block order vendor, AE, constructor, utility.

        Columns are matched by **header name** (normalized). If headers are missing (e.g. all
        ``Unnamed:``) but there are at least 32 columns, the same A–AF layout is read **by position**."""
        read_kw = dict(header=0, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        try:
            df = pd.read_csv(path, **read_kw)
        except UnicodeDecodeError:
            read_kw["encoding"] = "latin-1"
            df = pd.read_csv(path, **read_kw)

        if df.shape[1] <= 1 or df.shape[1] < 8:
            try:
                df = pd.read_csv(
                    path,
                    header=0,
                    sep=";",
                    dtype=str,
                    keep_default_na=False,
                    encoding="utf-8-sig",
                )
            except Exception:
                pass

        df = df.fillna("").reset_index(drop=True)
        nonempty = ~df.apply(lambda r: r.astype(str).str.strip().eq("").all(), axis=1)
        return df.loc[nonempty].reset_index(drop=True)

    @staticmethod
    def _scalar_str_cell(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ""
        return str(v).strip()

    def _inputs_from_positional_cost_risk_row(self, row, rn):
        """Parse one row using **fixed column indices 0..31** (Excel A–AF) for *cost_risk_inputs*.

        A–L (0–11): name, operating_time, design_time, build_time, commission_time, design_cost,
        build_cost, om_per_year, revenue_per_year, discount_rate, contingency, profit_margin.

        M–N (12–13): actual design / build progress (comma-separated cumulative %).
        O–P (14–15): target design / build progress (comma-separated).
        Q–T (16–19): design shares vendor, AE, constructor, utility.
        U–X (20–23): build shares (same actor order).
        Y–AB (24–27): O&M shares.
        AC–AF (28–31): revenue shares.
        """
        if len(row) < 32:
            raise ValueError(
                f"Row {rn}: cost_risk_inputs expects at least 32 columns (A–AF); this row has {len(row)}."
            )

        def gs(i):
            return self._scalar_str_cell(row.iloc[i])

        def rf(i, lab):
            s = gs(i)
            if not s:
                raise ValueError(f"Row {rn}: empty {lab} (column index {i}, 0=A).")
            return float(s)

        def ri(i, lab):
            return int(float(rf(i, lab)))

        name = gs(0) or f"row_{rn}"
        actual_design = self._parse_progress_cell(gs(12))
        actual_build = self._parse_progress_cell(gs(13))
        if not actual_design:
            raise ValueError(f"Row {rn}: actual design progress (column M / index 12) is empty.")
        if not actual_build:
            raise ValueError(f"Row {rn}: actual build progress (column N / index 13) is empty.")

        td_raw, tb_raw = gs(14), gs(15)
        target_design = self._parse_progress_cell(td_raw) if td_raw else list(actual_design)
        target_build = self._parse_progress_cell(tb_raw) if tb_raw else list(actual_build)

        return {
            "name": name,
            "operating_time": ri(1, "operating_time"),
            "design_time": ri(2, "design_time"),
            "build_time": ri(3, "build_time"),
            "commission_time": ri(4, "commission_time"),
            "design_cost": rf(5, "design_cost"),
            "build_cost": rf(6, "build_cost"),
            "om_per_year": rf(7, "om_per_year"),
            "revenue_per_year": rf(8, "revenue_per_year"),
            "discount_rate": rf(9, "discount_rate"),
            "contingency": rf(10, "contingency"),
            "profit_margin": rf(11, "profit_margin"),
            "actual_design_progress": actual_design,
            "actual_build_progress": actual_build,
            "target_design_progress": target_design,
            "target_build_progress": target_build,
            "design_shares": {
                "vendor": rf(16, "design share vendor (Q)"),
                "AE": rf(17, "design share AE (R)"),
                "constructor": rf(18, "design share constructor (S)"),
                "utility": rf(19, "design share utility (T)"),
            },
            "build_shares": {
                "vendor": rf(20, "build share vendor (U)"),
                "AE": rf(21, "build share AE (V)"),
                "constructor": rf(22, "build share constructor (W)"),
                "utility": rf(23, "build share utility (X)"),
            },
            "om_shares": {
                "vendor": rf(24, "O&M share vendor (Y)"),
                "AE": rf(25, "O&M share AE (Z)"),
                "constructor": rf(26, "O&M share constructor (AA)"),
                "utility": rf(27, "O&M share utility (AB)"),
            },
            "revenue_shares": {
                "vendor": rf(28, "revenue share vendor (AC)"),
                "AE": rf(29, "revenue share AE (AD)"),
                "constructor": rf(30, "revenue share constructor (AE)"),
                "utility": rf(31, "revenue share utility (AF)"),
            },
        }

    def _should_use_cost_risk_positional(self, df, lookup):
        """Use A–AF indices when we have 32+ columns but no recognizable *design_cost* header."""
        if df.shape[1] < 32:
            return False
        return self._norm_header("design_cost") not in lookup

    def _inputs_from_csv_row(self, df, row_idx):
        """Build PDSystems inputs: **cost_risk_inputs** A–AF layout (by header or by position)."""
        lookup = self._header_lookup(df)
        row = df.iloc[row_idx]
        rn = row_idx + 1

        if self._should_use_cost_risk_positional(df, lookup):
            return self._inputs_from_positional_cost_risk_row(row, rn)

        def f(*a, label=None):
            return self._cell_req_float(row, lookup, rn, *a, label=label)

        def i(*a, label=None):
            return self._cell_req_int(row, lookup, rn, *a, label=label)

        name = self._cell_raw(
            row,
            lookup,
            "name",
            "run_name",
            "descriptor",
            "project_name",
            "scenario",
            "case_id",
        ) or f"row_{rn}"

        actual_design = self._parse_progress_cell(
            self._cell_raw(
                row,
                lookup,
                "actual_design_progress",
                "actual_design",
                "design_progress_actual",
                "as_built_design_progress",
                "actual_design_progress_(%)",
            )
        )
        actual_build = self._parse_progress_cell(
            self._cell_raw(
                row,
                lookup,
                "actual_build_progress",
                "actual_build",
                "build_progress_actual",
                "as_built_build_progress",
                "actual_build_progress_(%)",
            )
        )
        if not actual_design:
            raise ValueError(f"Row {rn}: actual_design_progress is missing or empty.")
        if not actual_build:
            raise ValueError(f"Row {rn}: actual_build_progress is missing or empty.")

        td_raw = self._cell_raw(
            row,
            lookup,
            "target_design_progress",
            "target_design",
            "planned_design_progress",
            "baseline_design_progress",
            "target_design_progress_(%)",
        )
        tb_raw = self._cell_raw(
            row,
            lookup,
            "target_build_progress",
            "target_build",
            "planned_build_progress",
            "baseline_build_progress",
            "target_build_progress_(%)",
        )
        target_design = self._parse_progress_cell(td_raw) if td_raw else list(actual_design)
        target_build = self._parse_progress_cell(tb_raw) if tb_raw else list(actual_build)

        return {
            "name": name,
            "operating_time": i("operating_time", label="operating_time"),
            "design_time": i("design_time", label="design_time"),
            "build_time": i("build_time", label="build_time"),
            "commission_time": i("commission_time", label="commission_time"),
            "design_cost": f("design_cost", label="design_cost"),
            "build_cost": f("build_cost", label="build_cost"),
            "om_per_year": f("om_per_year", "OM_per_year", "o&m_per_year", label="om_per_year"),
            "revenue_per_year": f("revenue_per_year", label="revenue_per_year"),
            "discount_rate": f("discount_rate", label="discount_rate"),
            "contingency": f("contingency", label="contingency"),
            "profit_margin": f("profit_margin", label="profit_margin"),
            "actual_design_progress": actual_design,
            "actual_build_progress": actual_build,
            "target_design_progress": target_design,
            "target_build_progress": target_build,
            "design_shares": {
                "vendor": f("design_vendor", "vendor_design", label="design vendor share"),
                "AE": f("design_ae", "ae_design", label="design AE share"),
                "constructor": f("design_constructor", "constructor_design", label="design constructor share"),
                "utility": f("design_utility", "utility_design", label="design utility share"),
            },
            "build_shares": {
                "vendor": f("build_vendor", "vendor_build", label="build vendor share"),
                "AE": f("build_ae", "ae_build", label="build AE share"),
                "constructor": f("build_constructor", "constructor_build", label="build constructor share"),
                "utility": f("build_utility", "utility_build", label="build utility share"),
            },
            "om_shares": {
                "vendor": f("om_vendor", "vendor_om", label="O&M vendor share"),
                "AE": f("om_ae", "ae_om", label="O&M AE share"),
                "constructor": f("om_constructor", "constructor_om", label="O&M constructor share"),
                "utility": f("om_utility", "utility_om", label="O&M utility share"),
            },
            "revenue_shares": {
                "vendor": f("revenue_vendor", "vendor_rev", label="revenue vendor share"),
                "AE": f("revenue_ae", "ae_rev", label="revenue AE share"),
                "constructor": f("revenue_constructor", "constructor_rev", label="revenue constructor share"),
                "utility": f("revenue_utility", "utility_rev", label="revenue utility share"),
            },
        }

    def _apply_inputs_to_form(self, inputs):
        """Fill GUI entries from a PDSystems-style inputs dict (e.g. first CSV row)."""
        self.entries["name"].delete(0, tk.END)
        self.entries["name"].insert(0, str(inputs.get("name", "")))

        for k in (
            "operating_time",
            "design_time",
            "build_time",
            "commission_time",
            "design_cost",
            "build_cost",
            "revenue_per_year",
            "om_per_year",
            "discount_rate",
            "contingency",
            "profit_margin",
        ):
            self.entries[k].delete(0, tk.END)
            self.entries[k].insert(0, str(inputs[k]))

        for prog in (
            "actual_design_progress",
            "actual_build_progress",
            "target_design_progress",
            "target_build_progress",
        ):
            self.entries[prog].delete(0, tk.END)
            self.entries[prog].insert(0, ",".join(str(x) for x in inputs[prog]))

        for actor in ("vendor", "AE", "constructor", "utility"):
            self.share_entries[f"design_{actor}"].delete(0, tk.END)
            self.share_entries[f"design_{actor}"].insert(0, str(inputs["design_shares"][actor]))
            self.share_entries[f"build_{actor}"].delete(0, tk.END)
            self.share_entries[f"build_{actor}"].insert(0, str(inputs["build_shares"][actor]))
            self.share_entries[f"om_{actor}"].delete(0, tk.END)
            self.share_entries[f"om_{actor}"].insert(0, str(inputs["om_shares"][actor]))
            self.share_entries[f"revenue_{actor}"].delete(0, tk.END)
            self.share_entries[f"revenue_{actor}"].insert(0, str(inputs["revenue_shares"][actor]))

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

        try:
            inputs = self._inputs_from_csv_row(df, 0)
            self._apply_inputs_to_form(inputs)
        except Exception as e:
            self.loaded_df = None
            self.loaded_csv_path = None
            messagebox.showerror(
                "CSV header error",
                f"Could not map columns from the first data row:\n{e}\n\n"
                "Use **cost_risk_inputs** headers (e.g. design_cost, actual_design_progress, design_vendor) "
                "or 32+ columns A–AF with recognizable headers. See script docstring for layout.",
            )
            return

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

        for row_idx in range(len(df)):
            row = df.iloc[row_idx]

            try:
                inputs = self._inputs_from_csv_row(df, row_idx)

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
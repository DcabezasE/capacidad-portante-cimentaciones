"""
gui.py
======
Interfaz gráfica (Tkinter) para el cálculo de capacidad portante en
cimentaciones superficiales por los métodos de Terzaghi y Vesić.

Ejecutar desde la raíz del proyecto:
    python -m bearing_capacity.gui
o bien:
    python app.py
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from .core import (
    Method,
    FootingShape,
    FailureMode,
    SoilProfile,
    Foundation,
    Loads,
    WaterTable,
    compute_bearing_capacity,
)


# Mapas texto <-> enum para los combobox
SHAPE_MAP = {
    "Corrida (franja)": FootingShape.STRIP,
    "Cuadrada": FootingShape.SQUARE,
    "Circular": FootingShape.CIRCULAR,
    "Rectangular": FootingShape.RECTANGULAR,
}
METHOD_MAP = {
    "Terzaghi": Method.TERZAGHI,
    "Vesić": Method.VESIC,
    "Ambos (comparar)": "both",
}
FAILURE_MAP = {
    "General (suelo firme/denso)": FailureMode.GENERAL,
    "Local (suelo blando/suelto)": FailureMode.LOCAL,
}


class BearingCapacityApp(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=12)
        master.title("Capacidad Portante - Cimentaciones Superficiales")
        master.minsize(940, 640)
        self.grid(sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_input_panel()
        self._build_output_panel()
        self._toggle_fields()

    # ------------------------------------------------------------------ #
    # Panel de entrada
    # ------------------------------------------------------------------ #
    def _build_input_panel(self):
        frm = ttk.LabelFrame(self, text="Datos de entrada", padding=10)
        frm.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        row = 0

        # --- Método ---
        ttk.Label(frm, text="Método de cálculo").grid(row=row, column=0, sticky="w")
        self.method_var = tk.StringVar(value="Ambos (comparar)")
        cb = ttk.Combobox(
            frm, textvariable=self.method_var, state="readonly",
            values=list(METHOD_MAP.keys()), width=24,
        )
        cb.grid(row=row, column=1, sticky="ew", pady=2)
        cb.bind("<<ComboboxSelected>>", lambda e: self._toggle_fields())
        row += 1

        # --- Forma ---
        ttk.Label(frm, text="Forma de la zapata").grid(row=row, column=0, sticky="w")
        self.shape_var = tk.StringVar(value="Cuadrada")
        cb2 = ttk.Combobox(
            frm, textvariable=self.shape_var, state="readonly",
            values=list(SHAPE_MAP.keys()), width=24,
        )
        cb2.grid(row=row, column=1, sticky="ew", pady=2)
        cb2.bind("<<ComboboxSelected>>", lambda e: self._toggle_fields())
        row += 1

        # --- Geometría ---
        self.B_var = self._add_entry(frm, "Ancho B [m]", "1.5", row); row += 1
        self.L_lbl, self.L_entry, self.L_var = self._add_entry(
            frm, "Largo L [m]", "2.0", row, return_widgets=True
        ); row += 1
        self.Df_var = self._add_entry(frm, "Profundidad de desplante Df [m]", "1.0", row); row += 1

        ttk.Separator(frm, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8); row += 1

        # --- Suelo ---
        ttk.Label(frm, text="Propiedades del suelo", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w"); row += 1
        self.gamma_var = self._add_entry(frm, "γ natural [kN/m³]", "18.0", row); row += 1
        self.gsat_var = self._add_entry(frm, "γ saturado [kN/m³]", "20.0", row); row += 1
        self.phi_var = self._add_entry(frm, "Ángulo de fricción φ [°]", "30.0", row); row += 1
        self.c_var = self._add_entry(frm, "Cohesión c [kPa]", "0.0", row); row += 1

        ttk.Separator(frm, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8); row += 1

        # --- Nivel freático ---
        self.water_on = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frm, text="Considerar nivel freático", variable=self.water_on,
            command=self._toggle_fields,
        ).grid(row=row, column=0, columnspan=2, sticky="w"); row += 1
        self.dw_lbl, self.dw_entry, self.dw_var = self._add_entry(
            frm, "Prof. nivel freático dw [m] (desde superficie)", "1.0", row,
            return_widgets=True,
        ); row += 1

        ttk.Separator(frm, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8); row += 1

        # --- Terzaghi: modo de falla ---
        self.fail_lbl = ttk.Label(frm, text="Modo de falla (Terzaghi)")
        self.fail_lbl.grid(row=row, column=0, sticky="w")
        self.failure_var = tk.StringVar(value="General (suelo firme/denso)")
        self.fail_cb = ttk.Combobox(
            frm, textvariable=self.failure_var, state="readonly",
            values=list(FAILURE_MAP.keys()), width=24,
        )
        self.fail_cb.grid(row=row, column=1, sticky="ew", pady=2); row += 1

        # --- Vesić: opciones de factores ---
        self.depth_on = tk.BooleanVar(value=True)
        self.depth_chk = ttk.Checkbutton(
            frm, text="Vesić: usar factores de profundidad (d)",
            variable=self.depth_on)
        self.depth_chk.grid(row=row, column=0, columnspan=2, sticky="w"); row += 1

        self.incl_on = tk.BooleanVar(value=False)
        self.incl_chk = ttk.Checkbutton(
            frm, text="Vesić: usar factores de inclinación (i)",
            variable=self.incl_on, command=self._toggle_fields)
        self.incl_chk.grid(row=row, column=0, columnspan=2, sticky="w"); row += 1

        ttk.Separator(frm, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8); row += 1

        # --- Cargas (excentricidad / inclinación) ---
        ttk.Label(frm, text="Cargas (excentricidad / inclinación)",
                  font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w"); row += 1
        self.V_var = self._add_entry(frm, "Carga vertical V [kN]", "0.0", row); row += 1
        self.H_var = self._add_entry(frm, "Carga horizontal H [kN]", "0.0", row); row += 1
        self.Mb_var = self._add_entry(frm, "Momento → excentr. en B, Mb [kN·m]", "0.0", row); row += 1
        self.Ml_var = self._add_entry(frm, "Momento → excentr. en L, Ml [kN·m]", "0.0", row); row += 1

        ttk.Separator(frm, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8); row += 1

        # --- Factor de seguridad ---
        self.fs_var = self._add_entry(frm, "Factor de seguridad FS", "3.0", row); row += 1

        # --- Botón calcular ---
        ttk.Button(frm, text="Calcular", command=self.on_calculate).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    def _add_entry(self, parent, label, default, row, return_widgets=False):
        lbl = ttk.Label(parent, text=label)
        lbl.grid(row=row, column=0, sticky="w")
        var = tk.StringVar(value=default)
        ent = ttk.Entry(parent, textvariable=var, width=26)
        ent.grid(row=row, column=1, sticky="ew", pady=2)
        parent.columnconfigure(1, weight=1)
        if return_widgets:
            return lbl, ent, var
        return var

    # ------------------------------------------------------------------ #
    # Panel de salida
    # ------------------------------------------------------------------ #
    def _build_output_panel(self):
        frm = ttk.LabelFrame(self, text="Resultados", padding=10)
        frm.grid(row=0, column=1, sticky="nsew")
        frm.rowconfigure(0, weight=1)
        frm.columnconfigure(0, weight=1)

        self.output = tk.Text(frm, wrap="word", width=56, font=("Courier New", 10))
        self.output.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(frm, command=self.output.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.output.configure(yscrollcommand=sb.set, state="disabled")

    # ------------------------------------------------------------------ #
    # Habilitar / deshabilitar campos según selección
    # ------------------------------------------------------------------ #
    def _toggle_fields(self):
        shape = SHAPE_MAP[self.shape_var.get()]
        # Largo L solo para rectangular / corrida
        need_L = shape in (FootingShape.RECTANGULAR, FootingShape.STRIP)
        state_L = "normal" if need_L else "disabled"
        self.L_entry.configure(state=state_L)

        # Nivel freático
        state_w = "normal" if self.water_on.get() else "disabled"
        self.dw_entry.configure(state=state_w)

    # ------------------------------------------------------------------ #
    # Lectura de datos
    # ------------------------------------------------------------------ #
    def _read_float(self, var, name):
        try:
            return float(var.get())
        except ValueError:
            raise ValueError(f"'{name}' debe ser un número válido.")

    def _collect_inputs(self):
        shape = SHAPE_MAP[self.shape_var.get()]
        B = self._read_float(self.B_var, "Ancho B")
        Df = self._read_float(self.Df_var, "Df")
        L = None
        if shape in (FootingShape.RECTANGULAR, FootingShape.STRIP):
            L = self._read_float(self.L_var, "Largo L")

        fnd = Foundation(B=B, Df=Df, L=L, shape=shape)

        soil = SoilProfile(
            gamma=self._read_float(self.gamma_var, "γ natural"),
            gamma_sat=self._read_float(self.gsat_var, "γ saturado"),
            phi_deg=self._read_float(self.phi_var, "φ"),
            cohesion=self._read_float(self.c_var, "cohesión"),
        )

        loads = Loads(
            V=self._read_float(self.V_var, "V"),
            H=self._read_float(self.H_var, "H"),
            Mb=self._read_float(self.Mb_var, "Mb"),
            Ml=self._read_float(self.Ml_var, "Ml"),
        )

        if self.water_on.get():
            water = WaterTable(present=True, dw=self._read_float(self.dw_var, "dw"))
        else:
            water = WaterTable(present=False)

        FS = self._read_float(self.fs_var, "FS")
        if FS <= 0:
            raise ValueError("El factor de seguridad debe ser > 0.")

        failure = FAILURE_MAP[self.failure_var.get()]
        return fnd, soil, loads, water, FS, failure

    # ------------------------------------------------------------------ #
    # Cálculo y despliegue
    # ------------------------------------------------------------------ #
    def on_calculate(self):
        try:
            fnd, soil, loads, water, FS, failure = self._collect_inputs()
        except ValueError as e:
            messagebox.showerror("Error en los datos", str(e))
            return

        method_sel = METHOD_MAP[self.method_var.get()]
        methods = (
            [Method.TERZAGHI, Method.VESIC]
            if method_sel == "both"
            else [method_sel]
        )

        lines = []
        for m in methods:
            try:
                r = compute_bearing_capacity(
                    m, soil, fnd, loads=loads, water=water, FS=FS,
                    failure_mode=failure,
                    use_depth_factors=self.depth_on.get(),
                    use_inclination_factors=self.incl_on.get(),
                )
            except ValueError as e:
                lines.append(f"[{m.value.upper()}] ERROR: {e}\n")
                continue
            lines.append(self._format_result(r, fnd, FS))

        self._write_output("\n".join(lines))

    def _format_result(self, r, fnd, FS) -> str:
        f = r.factors
        out = []
        out.append("=" * 52)
        out.append(f"  MÉTODO: {r.method.value.upper()}")
        out.append("=" * 52)
        out.append(f"  Dimensiones efectivas: B'={r.B_eff:.3f} m  L'={r.L_eff:.3f} m")
        out.append("")
        out.append("  Factores de capacidad de carga:")
        out.append(f"    Nc = {f['Nc']:9.3f}")
        out.append(f"    Nq = {f['Nq']:9.3f}")
        out.append(f"    Nγ = {f['Ng']:9.3f}")
        out.append("")
        out.append("  Factores de forma / profundidad / inclinación:")
        out.append(f"    sc={f['sc']:.3f}  sq={f['sq']:.3f}  sγ={f['sg']:.3f}")
        out.append(f"    dc={f['dc']:.3f}  dq={f['dq']:.3f}  dγ={f['dg']:.3f}")
        out.append(f"    ic={f['ic']:.3f}  iq={f['iq']:.3f}  iγ={f['ig']:.3f}")
        out.append("")
        out.append("  Términos de la ecuación (kPa):")
        out.append(f"    Cohesión   : {f['term_cohesion']:10.2f}")
        out.append(f"    Sobrecarga : {f['term_sobrecarga']:10.2f}")
        out.append(f"    Peso suelo : {f['term_peso']:10.2f}")
        out.append(f"    q (sobrecarga efectiva) = {f['q_sobrecarga']:.2f} kPa")
        out.append(f"    γ efectivo (término peso) = {f['gamma_efectivo']:.2f} kN/m³")
        out.append("")
        out.append("  RESULTADOS:")
        out.append(f"    q_ult (bruta)     = {r.qu:10.2f} kPa")
        out.append(f"    q_ult (neta)      = {r.qu_net:10.2f} kPa")
        out.append(f"    q_adm (bruta)     = {r.q_adm:10.2f} kPa   [FS={FS}]")
        out.append(f"    q_adm (neta)      = {r.q_adm_net:10.2f} kPa")
        out.append(f"    Q_adm (carga)     = {r.Q_adm:10.2f} kN")
        out.append("")
        if r.notes:
            out.append("  Notas:")
            for n in r.notes:
                out.append(f"    - {n}")
        out.append("")
        return "\n".join(out)

    def _write_output(self, text: str):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")


def main():
    root = tk.Tk()
    try:
        # Tema más agradable si está disponible
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    BearingCapacityApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

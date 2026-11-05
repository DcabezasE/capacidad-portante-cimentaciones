"""
ejemplos.py
===========
Casos de prueba y validación del motor de cálculo de capacidad portante.

Ejecutar:
    python ejemplos.py

Incluye problemas tipo del libro de Das para verificar que los resultados
son coherentes con la bibliografía.
"""

from bearing_capacity.core import (
    Method, FootingShape, FailureMode,
    SoilProfile, Foundation, Loads, WaterTable,
    compute_bearing_capacity,
    terzaghi_bearing_factors, vesic_bearing_factors,
)


def separador(titulo):
    print("\n" + "=" * 60)
    print(f"  {titulo}")
    print("=" * 60)


def mostrar(r, FS):
    f = r.factors
    print(f"  Método: {r.method.value.upper()}")
    print(f"  B'={r.B_eff:.3f} m  L'={r.L_eff:.3f} m")
    print(f"  Nc={f['Nc']:.3f}  Nq={f['Nq']:.3f}  Nγ={f['Ng']:.3f}")
    print(f"  q_ult = {r.qu:8.2f} kPa   q_adm = {r.q_adm:8.2f} kPa  [FS={FS}]")
    print(f"  q_ult_neta = {r.qu_net:8.2f} kPa   Q_adm = {r.Q_adm:8.2f} kN")


# ---------------------------------------------------------------------------
def ejemplo_1():
    """Zapata cuadrada en arena. Comparación Terzaghi vs Vesić."""
    separador("Ejemplo 1: zapata cuadrada en arena (c=0)")
    print("  B=1.5 m, Df=1.0 m, φ=30°, γ=18 kN/m³, c=0, FS=3")
    soil = SoilProfile(gamma=18.0, phi_deg=30.0, cohesion=0.0)
    fnd = Foundation(B=1.5, Df=1.0, shape=FootingShape.SQUARE)
    for m in (Method.TERZAGHI, Method.VESIC):
        print()
        r = compute_bearing_capacity(m, soil, fnd, FS=3.0)
        mostrar(r, 3.0)


def ejemplo_2():
    """Zapata corrida en suelo cohesivo-friccionante (Terzaghi)."""
    separador("Ejemplo 2: zapata corrida, suelo c-φ (Terzaghi)")
    print("  B=1.2 m, Df=1.0 m, φ=25°, c=20 kPa, γ=17 kN/m³, FS=3")
    soil = SoilProfile(gamma=17.0, phi_deg=25.0, cohesion=20.0)
    fnd = Foundation(B=1.2, Df=1.0, shape=FootingShape.STRIP)
    r = compute_bearing_capacity(Method.TERZAGHI, soil, fnd, FS=3.0)
    print()
    mostrar(r, 3.0)


def ejemplo_3():
    """Efecto del nivel freático (Vesić)."""
    separador("Ejemplo 3: efecto del nivel freático (Vesić)")
    print("  Zapata cuadrada B=2 m, Df=1.5 m, φ=32°, γ=18, γsat=20.5, c=0")
    soil = SoilProfile(gamma=18.0, gamma_sat=20.5, phi_deg=32.0, cohesion=0.0)
    fnd = Foundation(B=2.0, Df=1.5, shape=FootingShape.SQUARE)
    casos = [
        ("Sin nivel freático", WaterTable(present=False)),
        ("NF en superficie (dw=0)", WaterTable(present=True, dw=0.0)),
        ("NF en la base (dw=Df=1.5)", WaterTable(present=True, dw=1.5)),
        ("NF dentro cuña (dw=2.5)", WaterTable(present=True, dw=2.5)),
        ("NF profundo (dw=10)", WaterTable(present=True, dw=10.0)),
    ]
    for nombre, w in casos:
        r = compute_bearing_capacity(Method.VESIC, soil, fnd, water=w, FS=3.0)
        print(f"  {nombre:30s} -> q_ult = {r.qu:8.2f} kPa")


def ejemplo_4():
    """Excentricidad de carga (Vesić)."""
    separador("Ejemplo 4: excentricidad de carga (Vesić)")
    print("  Zapata rectangular B=2 m, L=3 m, Df=1.2 m, φ=30°, c=0, γ=18")
    print("  Carga V=600 kN con momento Mb variable")
    soil = SoilProfile(gamma=18.0, phi_deg=30.0, cohesion=0.0)
    fnd = Foundation(B=2.0, L=3.0, Df=1.2, shape=FootingShape.RECTANGULAR)
    for Mb in (0.0, 100.0, 200.0):
        loads = Loads(V=600.0, Mb=Mb)
        r = compute_bearing_capacity(Method.VESIC, soil, fnd, loads=loads, FS=3.0)
        e = Mb / 600.0
        print(f"  Mb={Mb:6.1f} kN·m (e_B={e:.3f} m) -> "
              f"B'={r.B_eff:.3f}  q_ult={r.qu:8.2f} kPa  Q_adm={r.Q_adm:8.1f} kN")


def ejemplo_5():
    """Inclinación de carga (Vesić)."""
    separador("Ejemplo 5: inclinación de carga (Vesić)")
    print("  Zapata cuadrada B=2 m, Df=1.0 m, φ=30°, c=10 kPa, γ=18, V=500 kN")
    soil = SoilProfile(gamma=18.0, phi_deg=30.0, cohesion=10.0)
    fnd = Foundation(B=2.0, Df=1.0, shape=FootingShape.SQUARE)
    for H in (0.0, 50.0, 100.0):
        loads = Loads(V=500.0, H=H)
        r = compute_bearing_capacity(
            Method.VESIC, soil, fnd, loads=loads, FS=3.0,
            use_inclination_factors=True,
        )
        f = r.factors
        print(f"  H={H:6.1f} kN -> ic={f['ic']:.3f} iq={f['iq']:.3f} "
              f"iγ={f['ig']:.3f}  q_ult={r.qu:8.2f} kPa")


def ejemplo_6():
    """Falla general vs falla local (Terzaghi)."""
    separador("Ejemplo 6: falla general vs local (Terzaghi)")
    print("  Zapata cuadrada B=1.5 m, Df=1.0 m, φ=28°, c=15 kPa, γ=17")
    soil = SoilProfile(gamma=17.0, phi_deg=28.0, cohesion=15.0)
    fnd = Foundation(B=1.5, Df=1.0, shape=FootingShape.SQUARE)
    for modo in (FailureMode.GENERAL, FailureMode.LOCAL):
        r = compute_bearing_capacity(
            Method.TERZAGHI, soil, fnd, FS=3.0, failure_mode=modo)
        print(f"  Falla {modo.value:8s} -> q_ult={r.qu:8.2f} kPa  "
              f"q_adm={r.q_adm:8.2f} kPa")


def tabla_factores():
    """Imprime la tabla de factores N para verificación."""
    separador("Tabla de factores de capacidad de carga")
    print(f"  {'φ':>4} | {'Nc(T)':>8} {'Nq(T)':>8} {'Nγ(T)':>8} |"
          f" {'Nc(V)':>8} {'Nq(V)':>8} {'Nγ(V)':>8}")
    print("  " + "-" * 62)
    for phi in (0, 5, 10, 15, 20, 25, 30, 35, 40):
        tc, tq, tg = terzaghi_bearing_factors(phi)
        vc, vq, vg = vesic_bearing_factors(phi)
        print(f"  {phi:>4} | {tc:8.2f} {tq:8.2f} {tg:8.2f} |"
              f" {vc:8.2f} {vq:8.2f} {vg:8.2f}")


if __name__ == "__main__":
    tabla_factores()
    ejemplo_1()
    ejemplo_2()
    ejemplo_3()
    ejemplo_4()
    ejemplo_5()
    ejemplo_6()
    print("\n(Fin de los ejemplos)\n")

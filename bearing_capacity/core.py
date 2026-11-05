"""
core.py
=======
Motor de cálculo de capacidad portante en cimentaciones superficiales.

Implementa dos métodos:
  - Terzaghi (1943): ecuación clásica con factores de forma y distinción
    entre falla general y falla local.
  - Vesić (1973): ecuación general con factores de forma, profundidad e
    inclinación de carga.

Incluye correcciones por:
  - Nivel freático (ajuste del peso específico efectivo).
  - Excentricidad de carga/momento (método del área efectiva de Meyerhof).
  - Factor de seguridad -> capacidad admisible.

Unidades (consistentes en todo el módulo):
  - Longitudes  : metros [m]
  - Pesos esp.  : kN/m^3
  - Cohesión    : kPa  (kN/m^2)
  - Presiones   : kPa  (kN/m^2)
  - Fuerzas     : kN
  - Momentos    : kN*m
  - Ángulos     : grados en la interfaz, radianes internamente

Autor: proyecto de Geotecnia.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Tipos auxiliares
# ---------------------------------------------------------------------------
class FootingShape(str, Enum):
    """Geometría de la zapata."""
    STRIP = "corrida"        # franja continua (L >> B)
    SQUARE = "cuadrada"
    CIRCULAR = "circular"
    RECTANGULAR = "rectangular"


class FailureMode(str, Enum):
    """Modo de falla para el método de Terzaghi."""
    GENERAL = "general"      # suelo denso/firme
    LOCAL = "local"          # suelo suelto/blando -> se reducen c y phi


class Method(str, Enum):
    TERZAGHI = "terzaghi"
    VESIC = "vesic"


# ---------------------------------------------------------------------------
# Factores de capacidad de carga
# ---------------------------------------------------------------------------
def vesic_bearing_factors(phi_deg: float) -> tuple[float, float, float]:
    """
    Factores de capacidad de carga de Vesić (también usados por
    Hansen/Meyerhof para Nc y Nq).

        Nq = e^(pi*tan(phi)) * tan^2(45 + phi/2)
        Nc = (Nq - 1) * cot(phi)              (si phi=0 -> Nc = 5.14)
        Ng = 2 * (Nq + 1) * tan(phi)          (forma de Vesić)

    Devuelve (Nc, Nq, Ng).
    """
    phi = math.radians(phi_deg)

    if phi_deg == 0.0:
        Nq = 1.0
        Nc = 5.14  # = 2 + pi
        Ng = 0.0
        return Nc, Nq, Ng

    Nq = math.exp(math.pi * math.tan(phi)) * (math.tan(math.radians(45) + phi / 2.0)) ** 2
    Nc = (Nq - 1.0) / math.tan(phi)
    Ng = 2.0 * (Nq + 1.0) * math.tan(phi)
    return Nc, Nq, Ng


# Tabla oficial de factores de capacidad de carga de Terzaghi (falla general).
# Fuente: Terzaghi (1943), reproducida en Das, "Principles of Foundation
# Engineering". Columnas: phi [grados], Nc, Nq, Ng.
_TERZAGHI_TABLE = {
    0:  (5.70, 1.00, 0.00),
    1:  (6.00, 1.10, 0.01),
    2:  (6.30, 1.22, 0.04),
    3:  (6.62, 1.35, 0.06),
    4:  (6.97, 1.49, 0.10),
    5:  (7.34, 1.64, 0.14),
    6:  (7.73, 1.81, 0.20),
    7:  (8.15, 2.00, 0.27),
    8:  (8.60, 2.21, 0.35),
    9:  (9.09, 2.44, 0.44),
    10: (9.61, 2.69, 0.56),
    11: (10.16, 2.98, 0.69),
    12: (10.76, 3.29, 0.85),
    13: (11.41, 3.63, 1.04),
    14: (12.11, 4.02, 1.26),
    15: (12.86, 4.45, 1.52),
    16: (13.68, 4.92, 1.82),
    17: (14.60, 5.45, 2.18),
    18: (15.12, 6.04, 2.59),
    19: (16.56, 6.70, 3.07),
    20: (17.69, 7.44, 3.64),
    21: (18.92, 8.26, 4.31),
    22: (20.27, 9.19, 5.09),
    23: (21.75, 10.23, 6.00),
    24: (23.36, 11.40, 7.08),
    25: (25.13, 12.72, 8.34),
    26: (27.09, 14.21, 9.84),
    27: (29.24, 15.90, 11.60),
    28: (31.61, 17.81, 13.70),
    29: (34.24, 19.98, 16.18),
    30: (37.16, 22.46, 19.13),
    31: (40.41, 25.28, 22.65),
    32: (44.04, 28.52, 26.87),
    33: (48.09, 32.23, 31.94),
    34: (52.64, 36.50, 38.04),
    35: (57.75, 41.44, 45.41),
    36: (63.53, 47.16, 54.36),
    37: (70.01, 53.80, 65.27),
    38: (77.50, 61.55, 78.61),
    39: (85.97, 70.61, 95.03),
    40: (95.66, 81.27, 115.31),
    41: (106.81, 93.85, 140.51),
    42: (119.67, 108.75, 171.99),
    43: (134.58, 126.50, 211.56),
    44: (151.95, 147.74, 261.60),
    45: (172.28, 173.28, 325.34),
    46: (196.22, 204.19, 407.11),
    47: (224.55, 241.80, 512.84),
    48: (258.28, 287.85, 650.67),
    49: (298.71, 344.63, 831.99),
    50: (347.50, 415.14, 1072.80),
}


def terzaghi_bearing_factors(phi_deg: float) -> tuple[float, float, float]:
    """
    Factores de capacidad de carga de Terzaghi (falla general).

    Nq y Nc se obtienen de las expresiones cerradas de Terzaghi:
        Nq = e^((3*pi/2 - phi)*tan(phi)) / (2*cos^2(45 + phi/2))
        Nc = (Nq - 1) * cot(phi)          (phi=0 -> Nc = 5.7)

    Ng NO tiene una forma cerrada aceptada en Terzaghi, por lo que se toma
    de la TABLA oficial de Terzaghi (Das) con interpolación lineal. Esto
    evita las aproximaciones poco fiables y reproduce los valores de libro.

    Devuelve (Nc, Nq, Ng).
    """
    if phi_deg <= 0.0:
        return 5.70, 1.00, 0.00

    # Nq y Nc por fórmula cerrada de Terzaghi
    phi = math.radians(phi_deg)
    a = math.exp((3.0 * math.pi / 4.0 - phi / 2.0) * math.tan(phi))
    Nq = a ** 2 / (2.0 * (math.cos(math.radians(45) + phi / 2.0)) ** 2)
    Nc = (Nq - 1.0) / math.tan(phi)

    # Ng por interpolación de la tabla oficial
    Ng = _interp_table(_TERZAGHI_TABLE, phi_deg, index=2)
    return Nc, Nq, Ng


def _interp_table(table: dict, phi_deg: float, index: int) -> float:
    """Interpolación lineal de una columna de la tabla de Terzaghi."""
    lo = math.floor(phi_deg)
    hi = math.ceil(phi_deg)
    lo = max(0, min(50, lo))
    hi = max(0, min(50, hi))
    if lo == hi:
        return table[lo][index]
    v_lo = table[lo][index]
    v_hi = table[hi][index]
    frac = (phi_deg - lo) / (hi - lo)
    return v_lo + frac * (v_hi - v_lo)


# ---------------------------------------------------------------------------
# Factores de forma, profundidad e inclinación (Vesić / De Beer / Hansen)
# ---------------------------------------------------------------------------
def vesic_shape_factors(
    phi_deg: float, B_eff: float, L_eff: float, Nc: float, Nq: float
) -> tuple[float, float, float]:
    """
    Factores de forma de De Beer / Vesić en función de B'/L'.
    Para zapata corrida -> todos valen 1.0.
    Devuelve (sc, sq, sg).
    """
    phi = math.radians(phi_deg)
    ratio = B_eff / L_eff if L_eff > 0 else 1.0

    if phi_deg == 0.0:
        sc = 1.0 + 0.2 * ratio
        sq = 1.0
        sg = 1.0
        return sc, sq, sg

    sc = 1.0 + (Nq / Nc) * ratio
    sq = 1.0 + ratio * math.tan(phi)
    sg = 1.0 - 0.4 * ratio
    if sg < 0.6:
        sg = 0.6  # límite inferior práctico
    return sc, sq, sg


def vesic_depth_factors(
    phi_deg: float, Df: float, B: float
) -> tuple[float, float, float]:
    """
    Factores de profundidad de Hansen (usados por Vesić).
    Maneja el caso Df/B <= 1 y Df/B > 1 (con arctan en radianes).
    Devuelve (dc, dq, dg).
    """
    phi = math.radians(phi_deg)

    if B <= 0:
        return 1.0, 1.0, 1.0

    k = Df / B
    if k > 1.0:
        k = math.atan(Df / B)  # en radianes

    if phi_deg == 0.0:
        dc = 1.0 + 0.4 * k
        dq = 1.0
        dg = 1.0
        return dc, dq, dg

    dq = 1.0 + 2.0 * math.tan(phi) * (1.0 - math.sin(phi)) ** 2 * k
    dc = dq - (1.0 - dq) / (Nq_minus_one(phi_deg))
    dg = 1.0
    return dc, dq, dg


def Nq_minus_one(phi_deg: float) -> float:
    """Auxiliar: (Nq - 1)*tan(phi) usado en dc de Hansen."""
    phi = math.radians(phi_deg)
    _, Nq, _ = vesic_bearing_factors(phi_deg)
    val = (Nq - 1.0) * math.tan(phi)
    return val if abs(val) > 1e-9 else 1e-9


def vesic_inclination_factors(
    phi_deg: float,
    c: float,
    B_eff: float,
    L_eff: float,
    V: float,
    H: float,
    Nc: float,
) -> tuple[float, float, float]:
    """
    Factores de inclinación de carga de Vesić.

        H : componente horizontal de la carga [kN]
        V : componente vertical de la carga   [kN]

    Si H = 0 -> todos valen 1.0.
    Devuelve (ic, iq, ig).
    """
    if H <= 0.0 or V <= 0.0:
        return 1.0, 1.0, 1.0

    phi = math.radians(phi_deg)
    A_eff = B_eff * L_eff

    # exponente m (carga en la dirección de B)
    m = (2.0 + B_eff / L_eff) / (1.0 + B_eff / L_eff)

    if phi_deg == 0.0:
        # suelo puramente cohesivo
        ic = 1.0 - (m * H) / (A_eff * c * Nc) if c > 0 else 1.0
        iq = 1.0
        ig = 1.0
        return ic, iq, ig

    denom = V + A_eff * c / math.tan(phi)
    iq = (1.0 - H / denom) ** m
    ig = (1.0 - H / denom) ** (m + 1.0)
    # Fórmula estándar de Vesić para ic (derivada de iq):
    ic = iq - (1.0 - iq) / (Nc * math.tan(phi))

    for v in (ic, iq, ig):
        if v < 0:
            raise ValueError(
                "Factor de inclinación negativo: la carga horizontal es "
                "demasiado grande para la geometría/resistencia dadas."
            )
    return ic, iq, ig


# ---------------------------------------------------------------------------
# Factores de forma de Terzaghi (empíricos clásicos)
# ---------------------------------------------------------------------------
def terzaghi_shape_factors(shape: FootingShape) -> tuple[float, float, float]:
    """
    Factores de forma clásicos de Terzaghi (solo sc y sg; sq = 1).
        Corrida   : sc = 1.0 , sg = 1.0
        Cuadrada  : sc = 1.3 , sg = 0.8
        Circular  : sc = 1.3 , sg = 0.6
    Para rectangular se interpola linealmente con B/L (práctica común).
    Devuelve (sc, sq, sg).
    """
    if shape == FootingShape.STRIP:
        return 1.0, 1.0, 1.0
    if shape == FootingShape.SQUARE:
        return 1.3, 1.0, 0.8
    if shape == FootingShape.CIRCULAR:
        return 1.3, 1.0, 0.6
    # rectangular -> valores intermedios (se refinan fuera con B/L)
    return 1.3, 1.0, 0.8


# ---------------------------------------------------------------------------
# Entradas / Salidas
# ---------------------------------------------------------------------------
@dataclass
class SoilProfile:
    """Propiedades del suelo."""
    gamma: float            # peso específico natural (húmedo) [kN/m^3]
    phi_deg: float          # ángulo de fricción interna [grados]
    cohesion: float         # cohesión c [kPa]
    gamma_sat: Optional[float] = None   # peso específico saturado [kN/m^3]
    gamma_w: float = 9.81   # peso específico del agua [kN/m^3]

    def __post_init__(self):
        if self.gamma_sat is None:
            # estimación conservadora si no se da
            self.gamma_sat = self.gamma


@dataclass
class Foundation:
    """Geometría y profundidad de la cimentación."""
    B: float                       # ancho (menor dimensión) [m]
    Df: float                      # profundidad de desplante [m]
    L: Optional[float] = None      # largo [m] (None -> se deduce de shape)
    shape: FootingShape = FootingShape.STRIP

    def __post_init__(self):
        if self.shape == FootingShape.SQUARE:
            self.L = self.B
        elif self.shape == FootingShape.CIRCULAR:
            # diámetro = B; se trata como cuadrada equivalente en forma
            self.L = self.B
        elif self.shape == FootingShape.STRIP:
            self.L = self.L or 1000.0 * self.B  # L >> B
        elif self.L is None:
            raise ValueError("Zapata rectangular requiere especificar L.")


@dataclass
class Loads:
    """Cargas aplicadas."""
    V: float = 0.0          # carga vertical [kN] (para excentricidad/inclinación)
    H: float = 0.0          # carga horizontal [kN]
    Mb: float = 0.0         # momento alrededor del eje que genera excentr. en B [kN*m]
    Ml: float = 0.0         # momento que genera excentricidad en L [kN*m]


@dataclass
class WaterTable:
    """
    Posición del nivel freático medido desde la SUPERFICIE del terreno.
    dw = profundidad del nivel freático [m].
      - dw >= Df + B   -> agua muy profunda, sin efecto
      - Df <= dw < Df+B -> agua dentro de la cuña de falla
      - 0  <= dw < Df   -> agua por encima de la base
    Si no hay nivel freático, usar present=False.
    """
    present: bool = False
    dw: float = 1e9


@dataclass
class BearingResult:
    method: Method
    qu: float                      # capacidad portante última (bruta) [kPa]
    qu_net: float                  # capacidad portante última neta [kPa]
    q_adm: float                   # capacidad admisible (bruta) [kPa]
    q_adm_net: float               # capacidad admisible neta [kPa]
    Q_adm: float                   # carga admisible total [kN] (q_adm_net * A')
    B_eff: float
    L_eff: float
    factors: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Corrección por nivel freático
# ---------------------------------------------------------------------------
def water_table_correction(
    soil: SoilProfile, fnd: Foundation, water: WaterTable
) -> tuple[float, float, list[str]]:
    """
    Calcula:
      - q    : sobrecarga efectiva a la profundidad de desplante (término Nq)
      - g_eff: peso específico efectivo a usar en el término 0.5*gamma*B*Ng
    Devuelve (q, gamma_eff, notas).
    """
    notes: list[str] = []
    g = soil.gamma
    g_sat = soil.gamma_sat
    gw = soil.gamma_w
    g_prime = g_sat - gw  # peso específico sumergido (boyante)

    Df = fnd.Df
    B = fnd.B

    if not water.present:
        q = g * Df
        g_eff = g
        notes.append("Sin nivel freático: se usa gamma natural en ambos términos.")
        return q, g_eff, notes

    dw = water.dw

    # --- Término de sobrecarga q (hasta la base de la zapata, prof. Df) ---
    if dw <= 0:
        # agua en superficie
        q = g_prime * Df
        notes.append("NF en superficie: sobrecarga calculada con gamma'.")
    elif dw >= Df:
        # agua por debajo de la base -> sobrecarga con gamma natural
        q = g * Df
        notes.append("NF bajo la base: sobrecarga con gamma natural.")
    else:
        # agua entre superficie y base
        q = g * dw + g_prime * (Df - dw)
        notes.append(
            "NF entre superficie y base: sobrecarga = gamma*dw + gamma'*(Df-dw)."
        )

    # --- Peso específico efectivo para el término 0.5*gamma*B (zona de falla
    #     que se extiende ~B por debajo de la base) ---
    zone_bottom = Df + B
    if dw >= zone_bottom:
        g_eff = g
        notes.append("NF por debajo de la zona de falla (Df+B): gamma natural en 0.5*g*B.")
    elif dw <= Df:
        g_eff = g_prime
        notes.append("NF en o por encima de la base: gamma' en el término 0.5*g*B.")
    else:
        # agua dentro de la zona de falla -> interpolación lineal (Das)
        d = dw - Df
        g_eff = g_prime + (d / B) * (g - g_prime)
        notes.append(
            "NF dentro de la zona de falla: gamma efectivo interpolado "
            "gamma_eff = gamma' + (d/B)*(gamma - gamma')."
        )

    return q, g_eff, notes


# ---------------------------------------------------------------------------
# Excentricidad -> dimensiones efectivas (Meyerhof)
# ---------------------------------------------------------------------------
def effective_dimensions(fnd: Foundation, loads: Loads) -> tuple[float, float, list[str]]:
    """
    Aplica el método del área efectiva de Meyerhof.
        e_B = Mb / V ;  e_L = Ml / V
        B' = B - 2*e_B ;  L' = L - 2*e_L
    Si V = 0 no hay excentricidad.
    Devuelve (B_eff, L_eff, notas).
    """
    notes: list[str] = []
    B, L = fnd.B, fnd.L

    if loads.V <= 0 or (loads.Mb == 0 and loads.Ml == 0):
        return B, L, notes

    eB = loads.Mb / loads.V
    eL = loads.Ml / loads.V

    if eB > B / 6.0 or eL > L / 6.0:
        notes.append(
            f"ADVERTENCIA: excentricidad fuera del núcleo central "
            f"(e_B={eB:.3f}>B/6={B/6:.3f} o e_L={eL:.3f}>L/6={L/6:.3f}). "
            "Parte de la base trabaja a tracción; el método del área efectiva "
            "sigue siendo aplicable pero revisa el diseño."
        )

    B_eff = B - 2.0 * eB
    L_eff = L - 2.0 * eL

    if B_eff <= 0 or L_eff <= 0:
        raise ValueError(
            "La excentricidad es demasiado grande: dimensión efectiva <= 0. "
            "La resultante cae fuera de la zapata."
        )

    # Por convención B' debe ser la menor dimensión efectiva
    B_eff, L_eff = min(B_eff, L_eff), max(B_eff, L_eff)
    notes.append(
        f"Excentricidad: e_B={eB:.3f} m, e_L={eL:.3f} m -> "
        f"B'={B_eff:.3f} m, L'={L_eff:.3f} m (método de Meyerhof)."
    )
    return B_eff, L_eff, notes


# ---------------------------------------------------------------------------
# Cálculo principal
# ---------------------------------------------------------------------------
def compute_bearing_capacity(
    method: Method,
    soil: SoilProfile,
    fnd: Foundation,
    loads: Loads = Loads(),
    water: WaterTable = WaterTable(),
    FS: float = 3.0,
    failure_mode: FailureMode = FailureMode.GENERAL,
    use_depth_factors: bool = True,
    use_inclination_factors: bool = True,
) -> BearingResult:
    """
    Calcula la capacidad portante última y admisible.

    Parameters
    ----------
    method            : Method.TERZAGHI o Method.VESIC
    soil              : SoilProfile
    fnd               : Foundation
    loads             : Loads (para excentricidad e inclinación)
    water             : WaterTable
    FS                : factor de seguridad
    failure_mode      : solo aplica a Terzaghi (general/local)
    use_depth_factors : solo Vesić
    use_inclination_factors : solo Vesić
    """
    notes: list[str] = []

    # 1) Dimensiones efectivas por excentricidad
    B_eff, L_eff, nz = effective_dimensions(fnd, loads)
    notes += nz

    # 2) Nivel freático
    q_overburden, gamma_eff, nw = water_table_correction(soil, fnd, water)
    notes += nw

    c = soil.cohesion
    phi = soil.phi_deg

    # 3) Ajuste por falla local (solo Terzaghi)
    if method == Method.TERZAGHI and failure_mode == FailureMode.LOCAL:
        c = (2.0 / 3.0) * c
        phi = math.degrees(math.atan((2.0 / 3.0) * math.tan(math.radians(phi))))
        notes.append(
            "Falla local (Terzaghi): c* = 2/3*c y phi* = atan(2/3*tan(phi))."
        )

    # 4) Factores de capacidad
    if method == Method.TERZAGHI:
        Nc, Nq, Ng = terzaghi_bearing_factors(phi)
    else:
        Nc, Nq, Ng = vesic_bearing_factors(phi)

    # 5) Factores de forma / profundidad / inclinación
    if method == Method.TERZAGHI:
        sc, sq, sg = terzaghi_shape_factors(fnd.shape)
        dc = dq = dg = 1.0
        ic = iq = ig = 1.0
    else:
        sc, sq, sg = vesic_shape_factors(phi, B_eff, L_eff, Nc, Nq)
        if use_depth_factors:
            dc, dq, dg = vesic_depth_factors(phi, fnd.Df, fnd.B)
        else:
            dc = dq = dg = 1.0
        if use_inclination_factors:
            ic, iq, ig = vesic_inclination_factors(
                phi, c, B_eff, L_eff, loads.V, loads.H, Nc
            )
        else:
            ic = iq = ig = 1.0

    # 6) Ecuación general de capacidad portante (bruta)
    term_c = c * Nc * sc * dc * ic
    term_q = q_overburden * Nq * sq * dq * iq
    term_g = 0.5 * gamma_eff * B_eff * Ng * sg * dg * ig

    qu = term_c + term_q + term_g

    # 7) Capacidad neta y admisible
    qu_net = qu - q_overburden
    q_adm = qu / FS
    q_adm_net = qu_net / FS

    # Carga admisible total. Para zapata corrida, L es ficticio (L >> B),
    # por lo que se reporta la carga admisible POR METRO LINEAL (q_adm_net * B').
    if fnd.shape == FootingShape.STRIP:
        Q_adm = q_adm_net * B_eff          # kN por metro de longitud
        notes.append(
            "Zapata corrida: Q_adm está expresada POR METRO LINEAL "
            "de cimiento (kN/m)."
        )
    else:
        A_eff = B_eff * L_eff
        Q_adm = q_adm_net * A_eff          # kN (carga total)

    factors = {
        "Nc": Nc, "Nq": Nq, "Ng": Ng,
        "sc": sc, "sq": sq, "sg": sg,
        "dc": dc, "dq": dq, "dg": dg,
        "ic": ic, "iq": iq, "ig": ig,
        "q_sobrecarga": q_overburden,
        "gamma_efectivo": gamma_eff,
        "c_usada": c, "phi_usada": phi,
        "term_cohesion": term_c,
        "term_sobrecarga": term_q,
        "term_peso": term_g,
    }

    return BearingResult(
        method=method,
        qu=qu,
        qu_net=qu_net,
        q_adm=q_adm,
        q_adm_net=q_adm_net,
        Q_adm=Q_adm,
        B_eff=B_eff,
        L_eff=L_eff,
        factors=factors,
        notes=notes,
    )

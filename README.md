# Capacidad Portante en Cimentaciones Superficiales

Programa en **Python** para el cálculo de la capacidad portante (bearing
capacity) de cimentaciones superficiales por los métodos de **Terzaghi** y
**Vesić**, con interfaz gráfica.

Proyecto para la asignatura de **Geotecnia** (Ingeniería Civil).

---

## Características

- ✅ **Método de Terzaghi** (1943): factores de capacidad desde la tabla
  oficial, factores de forma clásicos y distinción entre **falla general**
  y **falla local** (reducción de c y φ).
- ✅ **Método de Vesić** (1973): ecuación general con factores de
  **forma (s)**, **profundidad (d)** e **inclinación de carga (i)**.
- ✅ **Nivel freático**: corrección del peso específico efectivo según la
  posición del agua (sobre la base, dentro de la cuña de falla, o por debajo).
- ✅ **Excentricidad de carga/momento**: método del área efectiva de Meyerhof
  (B' = B − 2·e_B, L' = L − 2·e_L).
- ✅ **Capacidad admisible** con factor de seguridad configurable
  (q_adm = q_ult / FS), capacidad bruta y neta, y carga admisible total.
- ✅ **Interfaz gráfica** en Tkinter (sin dependencias externas).
- ✅ Formas de zapata: corrida, cuadrada, circular y rectangular.

---

## Fundamento teórico

### Ecuación general de capacidad portante

```
q_ult = c·Nc·sc·dc·ic  +  q·Nq·sq·dq·iq  +  ½·γ·B'·Nγ·sγ·dγ·iγ
```

| Término        | Representa                                             |
|----------------|--------------------------------------------------------|
| `c·Nc·...`     | Contribución de la **cohesión** del suelo              |
| `q·Nq·...`     | Contribución de la **sobrecarga** (suelo sobre la base)|
| `½·γ·B'·Nγ·...`| Contribución del **peso** del suelo bajo la base       |

- **Terzaghi** no usa factores de profundidad ni de inclinación
  (`d = i = 1`); emplea factores de forma empíricos.
- **Vesić** usa la ecuación general completa.

### Factores de capacidad de carga

**Vesić:**
```
Nq = e^(π·tanφ) · tan²(45 + φ/2)
Nc = (Nq − 1)·cotφ            (φ=0 → Nc = 5.14)
Nγ = 2·(Nq + 1)·tanφ
```

**Terzaghi:** Nq y Nc por fórmula cerrada; Nγ interpolado de la tabla
oficial de Terzaghi (reproducida de Das).

### Nivel freático

El peso específico efectivo en el término `½·γ·B` se ajusta según la
posición del nivel freático `dw` (medido desde la superficie):

- `dw ≥ Df + B` → sin efecto, se usa γ natural.
- `Df ≤ dw < Df+B` → γ efectivo interpolado: `γ' + (d/B)·(γ − γ')`.
- `dw ≤ Df` → se usa γ' (sumergido) en el término de peso.

El término de sobrecarga `q` también se corrige según `dw`.

### Excentricidad (Meyerhof)

```
e_B = Mb / V        e_L = Ml / V
B'  = B − 2·e_B      L'  = L − 2·e_L
```

Se calcula la capacidad usando las dimensiones efectivas `B'` y `L'`.

---

## Requisitos

- Python **3.8+**
- **tkinter** (viene incluido en la instalación estándar de Python; en
  algunas distros de Linux se instala con `sudo apt install python3-tk`).

No requiere instalar librerías externas.

---

## Uso

### Interfaz gráfica

Desde la carpeta del proyecto:

```bash
python app.py
```

o bien:

```bash
python -m bearing_capacity.gui
```

Se abre una ventana donde se introducen los datos (geometría, suelo,
nivel freático, cargas, factor de seguridad), se elige el método
(Terzaghi, Vesić o ambos) y se pulsa **Calcular**.

### Como librería (en tus propios scripts)

```python
from bearing_capacity.core import (
    Method, FootingShape, SoilProfile, Foundation,
    Loads, WaterTable, compute_bearing_capacity,
)

soil = SoilProfile(gamma=18.0, gamma_sat=20.0, phi_deg=30.0, cohesion=0.0)
fnd  = Foundation(B=1.5, Df=1.0, shape=FootingShape.SQUARE)

r = compute_bearing_capacity(Method.VESIC, soil, fnd, FS=3.0)
print(f"q_ult = {r.qu:.1f} kPa")
print(f"q_adm = {r.q_adm:.1f} kPa")
```

### Ejemplos validados

```bash
python ejemplos.py
```

Ejecuta varios casos (incluidos problemas tipo del libro de Das) y
muestra los resultados para verificar el funcionamiento.

---

## Estructura del proyecto

```
.
├── app.py                      # Punto de entrada (abre la GUI)
├── ejemplos.py                 # Casos de prueba / validación
├── README.md
└── bearing_capacity/
    ├── __init__.py             # API del paquete
    ├── core.py                 # Motor de cálculo (Terzaghi y Vesić)
    └── gui.py                  # Interfaz gráfica (Tkinter)
```

---

## Unidades

| Magnitud          | Unidad     |
|-------------------|------------|
| Longitudes        | m          |
| Peso específico   | kN/m³      |
| Cohesión, presión | kPa (kN/m²)|
| Fuerzas           | kN         |
| Momentos          | kN·m       |
| Ángulos           | grados (°) |

---

## Referencias

- Das, B. M. *Principles of Foundation Engineering*.
- Terzaghi, K. (1943). *Theoretical Soil Mechanics*.
- Vesić, A. S. (1973). *Analysis of ultimate loads of shallow foundations*.

> Nota: herramienta de apoyo académico. Todo diseño real debe ser
> revisado por un ingeniero responsable.

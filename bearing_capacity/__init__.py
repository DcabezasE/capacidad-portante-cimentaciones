"""
Paquete de cálculo de capacidad portante en cimentaciones superficiales.

Módulos:
    core : motor de cálculo (Terzaghi y Vesić).
    gui  : interfaz gráfica en Tkinter.
"""
from .core import (
    Method,
    FootingShape,
    FailureMode,
    SoilProfile,
    Foundation,
    Loads,
    WaterTable,
    BearingResult,
    compute_bearing_capacity,
    terzaghi_bearing_factors,
    vesic_bearing_factors,
)

__all__ = [
    "Method",
    "FootingShape",
    "FailureMode",
    "SoilProfile",
    "Foundation",
    "Loads",
    "WaterTable",
    "BearingResult",
    "compute_bearing_capacity",
    "terzaghi_bearing_factors",
    "vesic_bearing_factors",
]

__version__ = "1.0.0"

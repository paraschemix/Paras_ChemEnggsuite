"""
utils/conversions.py
=====================
Centralized unit conversion matrices (SI <-> Imperial) used across all
calculation engines. Keeping conversions in one place avoids each of the
500+ tools re-implementing (and potentially mismatching) the same factors.
"""

# ---------------------------------------------------------------------
# Pressure
# ---------------------------------------------------------------------
def psi_to_pa(psi: float) -> float:
    return psi * 6894.757293168

def pa_to_psi(pa: float) -> float:
    return pa / 6894.757293168

def bar_to_psi(bar: float) -> float:
    return bar * 14.5037738

def psi_to_bar(psi: float) -> float:
    return psi / 14.5037738

def psia_to_psig(psia: float) -> float:
    return psia - 14.696

def psig_to_psia(psig: float) -> float:
    return psig + 14.696


# ---------------------------------------------------------------------
# Temperature
# ---------------------------------------------------------------------
def f_to_c(f: float) -> float:
    return (f - 32.0) * 5.0 / 9.0

def c_to_f(c: float) -> float:
    return c * 9.0 / 5.0 + 32.0

def f_to_r(f: float) -> float:
    return f + 459.67

def r_to_f(r: float) -> float:
    return r - 459.67

def c_to_k(c: float) -> float:
    return c + 273.15

def k_to_c(k: float) -> float:
    return k - 273.15


# ---------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------
def gpm_to_m3_s(gpm: float) -> float:
    return gpm * 6.30902e-5

def m3_s_to_gpm(m3_s: float) -> float:
    return m3_s / 6.30902e-5

def gpm_to_ft3_s(gpm: float) -> float:
    return gpm * 0.133681 / 60.0

def bpd_to_gpm(bpd: float) -> float:
    """Barrels per day to US gallons per minute (1 bbl = 42 US gal)."""
    return bpd * 42.0 / 1440.0


# ---------------------------------------------------------------------
# Length / Diameter
# ---------------------------------------------------------------------
def in_to_m(inches: float) -> float:
    return inches * 0.0254

def m_to_in(m: float) -> float:
    return m / 0.0254

def ft_to_m(ft: float) -> float:
    return ft * 0.3048

def m_to_ft(m: float) -> float:
    return m / 0.3048


# ---------------------------------------------------------------------
# Viscosity
# ---------------------------------------------------------------------
def cp_to_pas(cp: float) -> float:
    """Centipoise to Pascal-seconds."""
    return cp * 0.001

def pas_to_cp(pas: float) -> float:
    return pas / 0.001


# ---------------------------------------------------------------------
# Density
# ---------------------------------------------------------------------
def sg_to_lb_ft3(sg: float) -> float:
    """Specific gravity (water=1) to lb/ft3."""
    return sg * 62.428

def lb_ft3_to_sg(lb_ft3: float) -> float:
    return lb_ft3 / 62.428

def kg_m3_to_lb_ft3(kg_m3: float) -> float:
    return kg_m3 * 0.0624280

def lb_ft3_to_kg_m3(lb_ft3: float) -> float:
    return lb_ft3 / 0.0624280

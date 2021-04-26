from decimal import Decimal
import numpy

def calculate_delta(base, current):
    if not base or not current: return None
    return round(((current - base) / base) * Decimal(100), 4)

def f_talib(value):
    if numpy.isnan(value): return None
    return round(Decimal(value), 4)

def band(n, band):
    return round(round(n / Decimal(band)) * Decimal(band), 4)

def group_sma_o_p(n):
    if abs(n) <= 2: return band(n, .5)
    if abs(n) > 2: return band(n, 1)
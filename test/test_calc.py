from pytest import approx
from src.calc import calc_mass

#To Do:approxについて調べる(済み)
def test_calc_mass_baseline():
    expect = 1.55
    assert calc_mass(1, 1, 1, 0, 0, 1) == approx(expect, rel=1e-4)

def test_comparison_size():
    assert calc_mass(1, 1, 1, 0, 0, 1) <= calc_mass(2, 1, 1, 0, 0, 1)

def test_comparison_fat():
    assert calc_mass(1, 0.1, 1, 0, 0, 1) <= calc_mass(1, 0.9, 1, 0, 0, 1)

def test_comparison_skin():
    assert calc_mass(1, 0.1, 0.8, 0, 0, 0.3) <= calc_mass(1, 0.1, 0.8, 1, 0, 0.3)

def test_base():
    assert 1.0 <= calc_mass(1, 0.1, 0.15, 0.5, 0.15, 0.3) <= 1.5
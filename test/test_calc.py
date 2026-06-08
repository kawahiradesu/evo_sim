from pytest import approx
from src.calc import calc_mass, calc_grass_efficiency,calc_fermentation_bonus,calc_cold_resistance

"""calc_massのテスト"""
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

"""calc_grass_efficiencyのテスト"""

def test_fungs_effect():
    assert calc_grass_efficiency(0.5,0.5,0.5,0.1) >= calc_grass_efficiency(0.5,0.5,0.5,0.9)

def test_organ_effect():
    assert calc_grass_efficiency(0.8,0.5,0.5,0.5) >= calc_grass_efficiency(0.1,0.5,0.5,0.5)
    assert calc_grass_efficiency(0.5,0.8,0.5,0.5) >= calc_grass_efficiency(0.5,0.1,0.5,0.5)
    assert calc_grass_efficiency(0.5,0.5,0.8,0.5) >= calc_grass_efficiency(0.5,0.5,0.1,0.5)

def test_lowest_value():
    assert calc_grass_efficiency(0.0,0.0,0.0,0.0) >= 0.0
    assert calc_grass_efficiency(0.0,0.0,0.0,0.9) >= 0.0

"""calc_fermentation_bonusのテスト"""
def test_fermentation_scales_with_organ():
    assert calc_fermentation_bonus(0.5,0.5,0.8,0.5) >= calc_fermentation_bonus(0.5,0.5,0.1,0.5)
def test_fermentation_scales_with_microbiome(): 
    assert calc_fermentation_bonus(0.5,0.9,0.5,0.5) >= calc_fermentation_bonus(0.5,0.1,0.5,0.5)
def test_fermentation_requires_organ():   
    assert calc_fermentation_bonus(0.5,0.5,0.0,0.0) == 0.0
    assert calc_fermentation_bonus(0.5,0.9,0.0,0.0) == 0.0

"""calc_cold_resistanceのテスト"""
def test_fat_cold_resistance():
    assert calc_cold_resistance(0.9,0.5,0.5,0.5) >= calc_cold_resistance(0.1,0.5,0.5,0.5)
def test_hair_cold_resistance():
    assert calc_cold_resistance(0.5, 0.8, 0.0, 0.0) >= calc_cold_resistance(0.5, 0.8, 0.0, 0.9)
def test_fether_cold_resistance():
    assert calc_cold_resistance(0.5,0.8,1.0,1.0) >= calc_cold_resistance(0.5,0.8,1.0,0.0)
def test_Adaptation_value():
    assert 0.0 <= calc_cold_resistance(1.0,1.0,1.0,1.0) <= 1.0
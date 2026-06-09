from pytest import approx
from src.calc import calc_mass, calc_grass_efficiency,calc_fermentation_bonus,calc_cold_resistance,calc_armor_value,calc_genetic_distance,calc_morpho_distance
from src.config import *
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
    assert calc_fermentation_bonus(0.5,0.5,0.8,0.5,0.0) >= calc_fermentation_bonus(0.5,0.5,0.1,0.5,0.0)
def test_fermentation_scales_with_microbiome(): 
    assert calc_fermentation_bonus(0.5,0.9,0.5,0.5,0.0) >= calc_fermentation_bonus(0.5,0.1,0.5,0.5,0.0)
def test_fermentation_requires_organ():   
    assert calc_fermentation_bonus(0.5,0.5,0.0,0.0,0.0) == 0.0
    assert calc_fermentation_bonus(0.5,0.9,0.0,0.,0.0) == 0.0
# 臓器なし・腸ありでも微量の発酵が起きる
def test_fermentation_intestine_fallback():
    assert calc_fermentation_bonus(20.0, 0.9, 0.0, 0.0, 0.5) > 0.0

"""calc_cold_resistanceのテスト"""
def test_fat_cold_resistance():
    assert calc_cold_resistance(0.9,0.5,0.5,0.5) >= calc_cold_resistance(0.1,0.5,0.5,0.5)
def test_hair_cold_resistance():
    assert calc_cold_resistance(0.5, 0.8, 0.0, 0.0) >= calc_cold_resistance(0.5, 0.8, 0.0, 0.9)
def test_fether_cold_resistance():
    assert calc_cold_resistance(0.5,0.8,1.0,1.0) >= calc_cold_resistance(0.5,0.8,1.0,0.0)
def test_Adaptation_value():
    assert 0.0 <= calc_cold_resistance(1.0,1.0,1.0,1.0) <= 1.0

"""calc_armor_valueのテスト"""
def test_armor_amunt_keratin():
    assert calc_armor_value(0.9,0.5,0.5,0.5) >= calc_armor_value(0.1,0.5,0.5,0.5)

def test_armor_keratin_type():
    assert calc_armor_value(0.5,1.0,0.0,0.5) >= calc_armor_value(0.5,0.0,0.0,0.5)

def test_armor_size():
    assert calc_armor_value(0.5,0.5,0.5,2.0) >= calc_armor_value(0.5,0.5,0.5,0.5)

def test_armor_complexity():
    assert calc_armor_value(0.5,1.0,0.0,0.5) >= calc_armor_value(0.5,1.0,0.9,0.5)

"""calc_genetic_distance() と calc_morpho_distance()のテスト"""
def test_same_gen():
    assert calc_genetic_distance(
    0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
    0.5, 0.5, 0.5, 0.5, 0.5, 0.5
) == 0.0
    
def test_difference_gen():
    assert calc_genetic_distance(
    0.9, 0.1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
    0.5, 0.5, 0.5, 0.5, 0.5, 0.5
) != 0.0
    
def test_over_zero_gen():
    assert calc_genetic_distance(
    0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
    0.5, 0.5, 0.5, 0.5, 0.5, 0.5
) >= 0.0
    
def test_same_morpho():
    assert  calc_morpho_distance(
    0.5, 0.5, 0.5, 0.5,
    0.5, 0.5, 0.5, 0.5
) == 0.0

def test_comparison_gem_and_morpho():
    assert calc_genetic_distance(
    0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 0.0, 1.0, 0.0, 1.0, 0.5, 0.5,
    0.5, 0.5, 0.5, 0.5, 0.5, 0.5
) >= calc_morpho_distance(
    0.5, 0.5, 1.0, 1.0,
    0.5, 0.5, 0.5, 0.5
)
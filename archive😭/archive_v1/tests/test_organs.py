from evo_sim.archive_v1.entities.parts.organs import Heart


def test_heart_efficiency_without_septum():

    heart = Heart()

    heart.septum_development = 0

    assert heart.oxygen_transport_efficiency == 0.5


def test_heart_efficiency_four_chambered():
    heart = Heart()
    heart.septum_development = 1.0
    assert heart.oxygen_transport_efficiency == 1.2

from evo_sim.archive_v1.entities.parts.organs import StomachChamber

def test_stomach_becomes_fermenter():
    stomach = StomachChamber()

    stomach.acidity = 0.1
    stomach.stomach_capa = 0.4
    stomach.mutate()

    assert stomach.is_fermenter ==True

def test_stomach_weight():
    stomach = StomachChamber()

    stomach.stomach_capa = 0.5

    expected = stomach.weight + (0.5 * 0.5)

    assert stomach.total_weight == expected

import random
from evo_sim.archive_v1.entities.parts.organs import Stomachs

def test_stomach_chamder_growth(monkeypatch):
    def fake_random():
        return 0.01
    
    monkeypatch.setattr(random, "random", fake_random)

    stomachs = Stomachs()

    stomachs.mutate()

    assert len(stomachs.chambers) == 2

def test_has_rumen():
    stomach = Stomachs()

    chamber = stomach.chambers[0]

    chamber.is_fermenter = True

    assert stomach.has_rumen == True

from evo_sim.archive_v1.entities.parts.organs import Intestine

def test_hindgut_fermentation():
    
    intestine = Intestine()

    intestine.cecum_size =0.9

    intestine.mutate()

    assert intestine.has_hindgut_fermentation == True

def test_water_absorptation_lomit():
    intestine = Intestine()

    intestine.water_absorption = 2.0

    intestine.mutate()

    assert 0.0 <= intestine.water_absorption <= 1.0
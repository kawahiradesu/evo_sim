from evo_sim.archive_v2.genome import Genome
import evo_sim.archive_v2.traits_calc as traits_calc
import random
import evo_sim.archive_v2.traits_calc as traits_calc
import math

class Indevidual:
    __slot__ = ['genome', 'energy', 'is_alive','x','y','facing_angle']

    def __init__(self, parent_dna = None,start_x=0.0, start_y=0.0):
        #ゲノムの生成
        self.genome = Genome(parent_dna)
        self.energy = 100.0
        self.is_alive = True
        self.x = start_x
        self.y = start_y

        #最初はランダムな方向を向いて生まれる
        self.facing_angle = random.uniform(0, math.pi * 2)

    @property
    def dialy_cost(self):
        """1日に消費する基礎代謝を計算"""
        return traits_calc.cale_base_metabolism(self.genome.dna)
    
    def consume_energy(self):
        """一日の消費カロリーを計算！！０になったら餓死"""
        self.energy -= self.dialy_cost
        if self.energy <= 0:
            self.is_alive = False
            self.energy = 0

    
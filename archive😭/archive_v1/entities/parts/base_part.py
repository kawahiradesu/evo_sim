#base_part.py
import random

class Basepart:
    __slots__ = ['name', 'base_weight', 'mutation_rate']

    def __init__(self, name, weight=0.1):
        self.name = name
        self.base_weight = weight
        self.mutation_rate = 0.05

    def mutate_value(self, current_value, sigma=0.01):
        new_value = random.gauss(current_value, sigma)
        return max(0.0, new_value)

    def maybe_mutate(self, value):
        if random.random() < self.mutation_rate:
            return self.mutate_value(value)
        return value

    def mutate(self):
        pass

class InternalPart(Basepart):
    def __init__(self, name="内臓", weight=0.1):
        super().__init__(name=name, weight=weight)


class ExternalPart(Basepart):
    __slots__ = ['skin', 'fat']

    def __init__(self, name="外部パーツ", weight=0.5):
        super().__init__(name=name, weight=weight)
        self.skin = None
        self.fat = None

    def mutate(self):
        if self.skin:
            self.skin.mutate()
        if self.fat:
            self.fat.mutate()

    @property
    def total_weight(self):
        total = self.base_weight
        if self.skin:
            total += self.skin.total_weight
        if self.fat:
            total += self.fat.total_weight
        return total
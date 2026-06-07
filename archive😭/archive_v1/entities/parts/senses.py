from .base_part import ExternalPart
#senses.py

class Eye(ExternalPart):
    def __init__(self):
        super().__init__(name = "目", weight = 0.01)
        
        self.cornea_curvature = 0.5#角膜の湾曲
        self.pupil_control = 0.5#虹彩、瞳孔の収縮力
        self.eyelid_protection = 0.5#瞼の防御力
        self.retina_coler_ratio = 0.5#網膜の割り振り
        
        #self.has_tapetum = False
    """
    @property
    def night_vision(self):
        #暗視能力白黒特化でタペタムがあると跳ね上がる
        base_nigth = 1.0 - self.retina_coler_ratio
        return base_nigth * (2.0 if self.has_tapetum else 1.0)
    """

    def mutate_clamp(self, value):
        return max(0.0, min(1.0, self.mutate_value(value)))
    
    def mutate(self):
        self.cornea_curvature = self.mutate_clamp(self.cornea_curvature)
        self.pupil_control = self.mutate_clamp(self.pupil_control)
        self.eyelid_protection = self.mutate_clamp(self.eyelid_protection)
        self.retina_coler_ratio = self.mutate_clamp(self.retina_coler_ratio)
    

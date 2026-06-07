from .base_part import Basepart
import random

class Epidermis(Basepart):
    def __init__(self):
        super().__init__(name ="肌", weight= 0.0)
        #ケラチンの硬さのスペクトラム
        #~0.2(ケラチン無し)
        #~0.6(αケラチン)
        #~1.0(βケラチン)
        self.keratuin_hardess = 0.0
        self.corneum_development = 0.0
        self.feather=Feather()
        self.scole = Scale()
        self.skin = BareSkin()

        self.has_father = False
        self.has_scale = False
        self.has_bare_skin = False
   
    def mutate(self):
        self.keratuin_hardess = self.mutate_value(self.keratuin_hardess)
        self.corneum_development = self.mutate_value(self.corneum_development)

        self.keratuin_hardess = max(0.0, min(1.0, self.keratuin_hardess))
        self.corneum_development = max(0.0, min(1.0, self.corneum_development))
        
        if not self.has_father and 0.7 <= self.keratuin_hardess and (0.3 <= self.corneum_development <= 0.7):
            if random.random() < 0.05:
                self.has_father = True

        if not self.has_scale and 0.7 <= self.keratuin_hardess and 0.7 <= self.corneum_development:
            if random.random() < 0.05:
                self.has_scale = True
        if not self.has_bare_skin and (0.3 <= self.keratuin_hardess <= 0.6) and self.corneum_development <= 0.4:
            if random.random() < 0.05:
                self.has_bare_skin = True

    @property
    def totalweight(self):
        """表皮の総重量"""
        weight = self.base_weight

        if self.has_feather:
            weight += self.feather.weight
        if self.has_scole:
            weight += self.scole.weight
        if self.has_skin:
            weight += self.skin.weiht
class Feather(Basepart):
    def __init__(self,):
        super().__init__(name= "羽毛", weight = 0.01)
        self.coverage = 0.0
        self.density = 0.0

        self.length = 0.0
        self.hardness = 0.0
        self.branching = 0.0
        self.asymmetry = 0.0#この数値が高ければ高いほど飛行に有利
        self.pigmentation = 0.0
        self.powder_secretion = 0.0
        
    @property
    def is_decorative_feathers(self):
        return self.branching >= 0.7 and self.become_the_axis
         
    @property
    def become_the_axis(self):
        return self.hardness >= 0.6

    @property
    def is_down(self):
        return self.branching >= 0.3
    
    @property
    def differentiable(self):
        return self.length >= 0.3
    
    @property
    def is_bristle_feather(self):
        """
        剛毛羽ルート
        軸が極めて硬いのに枝分かれ（ふわふわ）が極限まで退化した状態
        哺乳類のヒゲのように物理的なセンサーとして機能したりハリネズミのような鎧として機能する
        """
        return self.become_the_axis and self.branching <= 0.1
    
    @property
    def is_powder_down(self):
        """
        粉綿羽ルート
        """

        return self.branching >= 0.3 and self.powder_secretion >= 0.5
    
    def dirt_resistance(self):
        """
        防汚力
        """
        if self.is_powder_down:
            return self.powder_secretion * self.coverage * 5.0
        return 0.0

    
    def mutate_clamp(self, value):
        return max(0.0, min(1.0, self.mutate_value(value)))

    def mutate(self):
        self.coverage = self.mutate_clamp(self.coverage)
        self.length = self.mutate_clap(self.length)
        self.hardness = self.mutate_clamp(self.hardness)
        self.density = self.mutate_clamp(self.density)
        self.pigmentation = self.mutate_clamp(self.pigmentation)

        if self.differentiable:
            self.branching = self.mutate_clamp(self.branching)
        if self.is_decorative_feathers:
            self.asymmetry = self.mutate_clamp(self.asymmetry)

class Scale(Basepart):
    def __init__(self):
        super().__init__(name = "鱗", weight = 0.1)
        self.coverage = 0.0
        self.thickness = 0.0
        self.overlap = 0.5
        self.osteoderm_level = 0.0#皮骨化
        #特殊な鱗(蛇型)
        self.directional_grip = 0.0

    @property
    def is_ventral_scale(self):
        return self.overlap >= 0.7 and self.directional_grip >= 0.6

    def mutate_clamp(self, value):
        return max(0.0, min(1.0, self.mutate_value(value)))

    def mutate(self):
        self.coverage = self.mutate_clamp(self.coverage)
        self.thickness = self.mutate_clamp(self.thickness)
        self.overlap = self.mutate_clamp(self.overlap)
        if self.is_ventral_scale :
            self.directional_grip = self.mutate_clamp(self.directional_grip)

    @property
    def slithering_propulsion(self):
        if self.is_ventral_scale:
            return self.directional_grip * self.coverage * 5.0
        return 0.0

class BareSkin(Basepart):
    def __init__(self):
        super().__init__(name ="肌と獣毛", weight = 0.02)

        self.coverage = 0.0
        self.hair_thickness = 0.0
        self.hair_density = 0.0
        self.sweat_gland = 0.0

        self.skin_pigmentation = 0.0
        self.sebum_gland = 0.0
        self.hair_pigmentation = 0.0

    @property
    def visible_pigmentation(self):
        fur_visibility = self.hair_density * self.coverage

        if fur_visibility >= 0.5:
            return self.hair_pigmentation
        
        else:
            return self.skin_pigmentation
#organs.py
from .base_part import InternalPart
import random
"""
肺
"""
class Lung(InternalPart):
    def __init__(self,):
        super().__init__(name = "肺", weight = 0.05)

        self.capacity = 1.0
        self.surface_area =1.0
        self.diaphragm_power = 0.0
        self.air_sacs_power = 0.0
        #進化フラグ
        self.has_diaphragm = False
        self.has_air_sacs = False

    def mutate(self):
        self.capacity = self.mutate_value(self.capacity)
        self.surface_area = self.mutate_value(self.surface_area)
        if self.has_diaphragm:
            self.diaphragm_power = self.mutate_value(self.diaphragm_power)
        if self.has_air_sacs:
            self.air_sacs_power = self.mutate_value(self.air_sacs_power)

class Heart(InternalPart):
    def __init__(self,):
        super().__init__(name = "心臓", weight=0.05)
        self.septum_development = 0.0 #初期値は０(2心房1心室)
        self.muscle_power = 1.0


    @property
    def is_four_chambered(self):

        return self.septum_development >= 1.0

    def mutate(self):
        self.muscle_power = self.mutate_value(self.muscle_power)
        if not self.is_four_chambered:
            self.septum_development = self.mutate_value(self.septum_development)
            self.septum_development = max(0.0, min(1.0, self.septum_development))

    @property
    def oxygen_transport_efficiency(self):
        """吸った酸素をどれだけ筋肉に届けられるのかの倍率"""
        if self.is_four_chambered:
            return 1.2
        
        else:
            #壁が未完成だとペナルティ
            #壁がない時には50%の効率、壁が伸びるにつれて最大90%まで効率が伸びる
            return 0.5 +(self.septum_development * 0.4)

class StomachChamber(InternalPart):
    def __init__(self, name ="胃", is_true_stomach= True):
        super().__init__(name =name, weight= 0.1)
        self.stomach_capa = 0.5 if is_true_stomach else 0.05
        self.acidity = 0.6 if is_true_stomach else 0.0
        

        #--複数の胃--
        self.is_fermenter = False#反芻ができるのかフラグ

    def mutate(self):
        self.stomach_capa = self.mutate_value(self.stomach_capa)
        self.acidity = self.mutate_value(self.acidity)
        #この部屋で草を発酵できるのか。（胃酸が弱くて容量が大きくバクテリアが住みやすい）
        if self.acidity < 0.2 and self.stomach_capa > 0.3:
            self.is_fermenter = True

    @property
    def total_weight(self):
        return self.weight + (self.stomach_capa * 0.5)
    
class Stomachs(InternalPart):
    def __init__(self):
        super().__init__(name="胃群", weight=0.0)

        self.chambers = [StomachChamber(name="胃群(主胃)", is_true_stomach=True)]

        #胃石は胃全体で管理する
        self.gastrolith = 0.0
        self.has_gastrolith = False

    def mutate(self):
        #今あるすべての部屋を個別に
        for chambers in self.chambers:
            chambers.mutate()

        if random.random() < 0.05 and len(self.chambers) < 4:
            new_num = len(self.chambers) + 1
            self.chambers.append(StomachChamber(name=f"第{new_num}胃", is_true_stomach = False))
    @property
    def total_weight(self):
        #すべての部屋の重さの合計 +　胃石の重さ
        Chamber_weight = sum([c.total_weight for c in self.chambers])
        return Chamber_weight + self.gastrolith
    
    @property
    def has_rumen(self):
        return any(c.is_fermenter for c in self.chambers)
class Intestine(InternalPart):
    def __init__(self,):
        super().__init__(name = "腸", weight = 0.15)
        self.length = 0.4

        #--植物食--
        self.cecum_size = 0.1
        self.has_hindgut_fermentation = False

        #水分吸収
        self.water_absorption = 0.1

    def mutate(self):
        self.length = self.mutate_value(self.length)
        self.cecum_size = self.mutate_value(self.cecum_size)
        #盲腸が植物の消化に役立つか。
        if self.cecum_size >= 0.8:
            self.has_hindgut_fermentation = True
        self.water_absorption = self.mutate_value(self.water_absorption)
        self.water_absorption = max(0.0, min(1.0, self.water_absorption))

    @property
    def total_weight(self):
        return super().weight + (self.length * 0.5) + (self.cecum_size*0.3)
    

class Fat(InternalPart):
    def __init__(self):
        super().__init__(name= "脂肪", weight = 0.0)
        #脂肪のつき方
        #0.0一点集中~1.0全身パック
        self.distribution = 0.5

    def mutate(self):
        self.distribution = self.mutate_value(self.distribution)

class Liver(InternalPart):
    def __init__(self):
        super().__init__(name = "肝臓", weight= 0.3)
        #グリコーゲンの貯蔵量
        self.glycogen_capacity = 0.5

        #解毒能力
        self.detox_power = 0.1

    def mutate(self):
        self.glycogen_capacity = self.mutate_value(self.glycogen_capacity)
        self.detox_power = self.mutate_value(self.detox_power)

    @property
    def total_weight(self):
        #肝臓の性能が高ければ高いほど分厚くなる
        #さらに肝臓は基礎代謝を爆食いする
        return self.weight + (self.glycogen_capacity*0.3) + (self.detox_power*0.4)

class NervousSystem(InternalPart):
    def __init__(self):
        super().__init__(name="神経系", weight=0.05)
        # 脳のキャパシティ（総ポイント）だけを持つ
        self.capacity = 70.0 
        self.axon_capa = 0.4
        self.cover = 0.0

    def mutate_clamp(self, value):
        return max(0.0, min(1.0, self.mutate_value(value)))

    @property
    def get_myelin_multiplier(self,is_warm_blooded):
        if is_warm_blooded :
            if self.cover >= 0.8:
                return 10.0
        else:
            return 1.0
    def mutate(self):
        self.capacity = self.mutate_clamp(self.capacity)
        self.axon_capa = self.mutate_clamp(self.axon_capa)

       
    @property
    def caloric_cost(self, used_points, has_myelin_active):
        base_cost = used_points * 1.5
        if has_myelin_active:
            base_cost * 2.0
        return base_cost
    



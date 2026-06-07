#skeleton.py
from .base_part import ExternalPart

"""
ここからは足だよ！！！！！！！！
"""
class Leg(ExternalPart):
    def __init__(self):
        super().__init__(name="前脚",weight=0.0)

        self.up_leg = Upper_leg()
        self.low_leg = Lower_leg()
        self.foot = Foot()
        self.knee_angle_horizontal = 0.5#横方向の可動域*180で90だからイクチオステガの初期値は0.5
        self.knee_angle_vertical = 0.3#縦方向の可動域
        #今後ディスプレイとかひれを拡張するかも。
    def mutate(self):
        self.up_leg.mutate()
        self.low_leg.mutate()
        self.foot.mutate()
        self.knee_angle_horizontal = self.mutate_value(self.knee_angle_horizontal)
        self.knee_angle_vertical = self.mutate_value(self.knee_angle_vertical)
    @property
    def total_weight(self):
        # 足先の重さも忘れずに足してあげよう！
        return self.up_leg.total_weight + self.low_leg.total_weight + self.foot.total_weight

    @property
    def length(self):
        # return を追加！
        return self.up_leg.length + self.low_leg.length
        
class Upper_leg(ExternalPart):
    def __init__(self):
        super().__init__(name = "上腕", weight = 0.3)
        self.length = 0.5
        self.strength = 0.2
        
    def mutate(self):
        self.length = self.mutate_value(self.length)
        self.strength = self.mutate_value(self.strength)
        
class Lower_leg(ExternalPart):
    def __init__(self):
        super().__init__(name = "下腿", weight = 0.1)
        self.length = 0.5
        self.strength = 0.1
        
    def mutate(self):
        self.length = self.mutate_value(self.length)
        self.strength = self.mutate_value(self.strength)
        
class Foot(ExternalPart):
    def __init__(self):
        super().__init__(name="前足全体の形質", weight=0.1)

        self.gcd = 0.8
        self.sole = Sole()
        self.ground_angle = 1.0
        #指を4つ生成（親指、人差し指、中指、外指）
        self.fingers = [Finger()for _ in range(4)]

    @property
    def total_weight(self):
        """
       土台の重さ＋足裏の重さ＋四本の指
        """
        finger_weight = sum(f.total_weight +f.nail.total_weight for f in self.fingers)
        return super().total_weight + self.sole.total_weight + finger_weight
    
    def mutate(self):
    
        self.gcd = self.mutate_value(self.gcd)
        self.sole.mutate()
        self.ground_angle = self.mutate_value(self.ground_angle)
        for finger in self.fingers:
            finger.mutate()

    @property
    def support_power(self):
        """
        手のひら＋指＋爪の接地力を合計して返す
        """

        #手のひらの接地度
        palm_support = self.sole.area*self.sole.contact_style

        #指の接地度
        Finger_support = sum(f.length*f.width for f in self.fingers if f.area > 0.5)
        #爪の接地度
        nail_support = sum(f.nail.length * 0.5 for f in self.fingers if self.sole.contact_style < 0.3)

        return palm_support + Finger_support + nail_support
class Nail(ExternalPart):
    def __init__(self):
        super().__init__(name="爪",weight=0.01)
        self.length= 0.0
        self.nail_sharpness = 0.7

    def mutate(self):
        self.length = self.mutate_value(self.length)
        self.nail_sharpness = self.mutate_value(self.nail_sharpness)

class Sole(ExternalPart):
    def __init__(self):
        super().__init__(name="足の裏", weight=0.1)
        self.hardness = 0.5
        self.cushion = 0.1
        self.finger_distance = 0.5
         #指と指の間の距離感、もしくは設置している指の端から端までの幅の長さ
        self.pad_thickness = 0.2
        self.grip_texture = 0.2
        self.mobility = 0.5
        self.contact_style = 1.0
        self.area = 0.4
    def mutate(self):
        self.hardness=self.mutate_value(self.hardness)
        self.cushion=self.mutate_value(self.cushion)
        self.finger_distance = self.mutate_value(self.finger_distance)
        self.pad_thickness = self.mutate_value(self.pad_thickness)
        self.grip_texture = self.mutate_value(self.grip_texture)
        self.mobility = self.mutate_value(self.mobility)
        self.contact_style = self.mutate_value(self.contact_style)
        self.area = self.mutate_value(self.area)

class Finger(ExternalPart):
    def __init__(self):
        super().__init__(name="指", weight=0.01)
        self.strength = 0.3
        self.length = 0.5
        self.rom_up = 0.2
        #rom = range of motion
        self.rom_down = 0.1
        self.width = 0.2
        self.nail = Nail()
        self.area = 1.0

    def mutate(self):
        self.strength = self.mutate_value(self.strength)
        self.length = self.mutate_value(self.length)
        self.rom_up = self.mutate_value(self.rom_up)
        self.rom_down = self.mutate_value(self.rom_down)
        self.width = self.mutate_value(self.width)
        self.area = self.mutate_value(self.area)
        self.nail.mutate()

"""
ここからが肩だよ！！！
"""
class Sholder(ExternalPart):
    def __init__(self):
        super().__init__(name = "肩帯", weight = 0.1)
        self.scapula_size = 0.5#大きいほど腕の力にボーナス（肩甲骨）
        self.clavicle_size = 0.1#大きいほど腕の大きさを広げられる。
        self.front_join_angle = 0.0                        #肩からの腕の生え方

    def mutate(self):
        self.scapula_size =self.mutate_value(self.scapula_size)
        self.clavicle_size = self.mutate_value(self.clavicle_size)
        self.front_join_angle = self.mutate_value(self.front_join_angle)

"""
ここが骨盤
"""
class Pelvis(ExternalPart):
    def __init__(self):
        super().__init__(name = "骨盤", weight = 0.15)
        self.ilium_robustaness = 0.5 #頑丈なほど重い体重を支えられる
        self.ischium_length = 0.4 #長いほど蹴り出す力が強い
        self.hip_joint_angle = 0.0 #0だとトカゲのように足が横に突き出る。
        
    def mutate(self):
        self.ilium_robustaness = self.mutate_value(self.ilium_robustaness)
        self.ischium_length = self.mutate_value(self.ischium_length)
        self.hip_joint_angle = self.mutate_value(self.hip_joint_angle)

"""
ここからが胴体だよ！！！！
"""
class Torso(ExternalPart):
    def __init__(self):
        super().__init__(name = "胴体", weight=2.0)

        #物理的なサイズ
        self.length = 1.0 #肩から腰までの距離
        self.width = 0.6#胴体の横幅
        
        #背骨の進化
        self.flex_lateral = 0.5 #背骨の左右のしなやかさ
        self.flex_sagittal = 0.1#背骨の前後のしなやかさ
        
        #肋骨の性質(主に内臓に関与する)
        self.rib_cage_size = 0.5#肋骨の広がり
        self.rib_sagittal = 0.5#肋骨の柔軟性

        #骨の頑丈さ
        self.bone_density = 1.0#骨密度
        self.structural_optimization = 0.2#構造の最適化(トラス構造など)

        self.marrow_activity = 0.5#骨髄の活動量

    def mutate(self):
        self.length = self.mutate_value(self.length)
        self.width = self.mutate_value(self.width)
        self.flex_lateral = self.mutate_value(self.flex_lateral)
        self.flex_sagittal = self.mutate_value(self.flex_sagittal)
        self.rib_cage_size = self.mutate_value(self.rib_cage_size)
        self.rib_sagittal = self.mutate_value(self.rib_sagittal)
        self.bone_density = self.mutate_value(self.bone_density)
        self.structural_optimization = self.mutate_value(self.structural_optimization)
        self.marrow_activity = self.mutate_value(self.marrow_activity)

    @property
    def oxygen_carrying_capacity(self):
        marrow_space = 1.0 - (self.marrow_activity * 0.8)

        return marrow_space * self.marrow_activity * 10

    @property
    def weight(self):
        base_w = (self.length * self.width * self.rib_cage_size)
        return base_w * self.bone_density
    
    @property
    def robustness(self):
        return (self.bone_density * self.rib_cage_size) *(1.0 + self.structural_optimization)
    
"""
ここからが尻尾だよ
"""
class Tail(ExternalPart):
    def __init__(self):
        super().__init__(name ="尻尾", weight = 0.5)
        self.length = 0.5#長さ
        self.base_thickness = 0.3#根元の太さ
        self.flexibility = 0.5#しなやかさ
        self.grip_power = 0.0
        self.power_to_stand = 0.0

    @property
    def is_prehensile(self):
        return self.flexibility > 0.8 and self.length > 0.6
    
    @property
    def is_tripod_tail(self):
        return self.length > 0.6 and self.base_thickness > 0.7

    def mutate_clamp(self, value):
        return max(0.0, min(1.0, self.mutate_value(value)))
    
    @property
    def dynamic_balance(self):
        """チータールート"""
        #長くてしなやかであるほどスコアが出る
        return self.length * self.flexibility *10
    
    @property
    def gyro_stapilizer(self):
        """ラプトル的な尾"""
        stiffness =1.0 - self.flexibility
        moment_of_inertia = (self.base_thickness * (self.length**2))
        return moment_of_inertia * stiffness * 10
    
    def mutate(self):
        self.length = self.mutate_clamp(self.length)
        self.base_thickness = self.mutate_clamp(self.base_thickness)
        self.flexibility = self.mutate_clamp(self.flexibility)
        if self.is_prehensile:
            self.grip_power = self.mutate_clamp(self.grip_power)
        if self.is_can_stand:
            self.power_to_stand = self.mutate_clamp(self.power_to_stand)

        
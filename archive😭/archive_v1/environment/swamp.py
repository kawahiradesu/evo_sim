#swamp.py
from .base_envi import Baseenvi

class Swamp(Baseenvi):
    def __init__(self):
        super().__init__(
            name = "デボン紀の沼地",
            water_depth = 0.12, 
            ground_softness = 0.7,
            angiosperm_density = 0.0,
            gymnosperm_density = 0.2,
            prey_density =  0.8            
        ) 
        #餌の総量
        self.insect_stock = 1000
        self.fish_stock = 1000
        #[沼地]の見た目やゾーンを追加
        self.water_y_line = 500
        self.water_color = (0, 100 , 200)
        self.land_color = (139 , 69 ,19)

    def get_terrain_at(self, y):
        """座標から地形を特定"""
        return "WATER" if y >self.water_y_line else "LAND"

    def calculate_speed(self, ind):
        """
        個体スペックから2D空間での物理性能を算出する
        """
        # 推進力の計算
        #前後の上腕・下腕の合計を筋肉量と仮定
        leg_power = (ind.front_leg.up_leg.length +ind.front_leg.low_leg.length+
                     ind.back_leg.up_leg.length + ind.back_leg.low_leg.length)
        #抵抗の計算(対向による恩恵)
        #体高が推進より高ければスイスイ動ける
        clearance = ind.front_body_height - self.water_depth
        drag_reduction = max(0.1,clearance)
        #最終的なスピード
        #パワーに比例、重さに反比例、抵抗軽減が乗算
        speed = (leg_power / max(0.1,ind.total_weight)) *  drag_reduction * 10.0
        #地形効果
        terrain = self.get_terrain_at(ind.pos.y)
        if terrain == "LAND":
            speed *= 0.6
        return speed
    def refresh_resources(self):
        self.insect_stock = min(1000, self.insect_stock + 5)
        self.fish_stock = min(1000, self.fish_stock + 5)
    def evaluate(self, ind):
        """
        沼地サバイバルの基準点
        """
        weight =ind.total_weight
        total_power = ind.front_leg.foot.support_power + ind.back_leg.foot.support_power
        h_front = ind.front_body_height
        h_back = ind.back_body_height
        
        avg_heigth = (h_front + h_back) /2.0

        #干からびメソッド
        if ind.hydration <= 0:
            return 0.0
        
        if ind.energy <= 0:
            return 0.0
        
        # 2. 沈み込みペナルティ
        #柔らかい地面ほど接地力が必要。足りないとsinkが発生
        #重い個体ほどより高い接地度が要求される
        sink = max(0,weight-(total_power*(2.0 - self.ground_softness)))
       
        
        #3.実質的な足の長さ
        #沈んだ分だけ、水面から出ている足が短くなる
        #平均的な高さより沈んだら「お腹で支える」状態になる。
        is_belly_rub = avg_heigth < sink
        if is_belly_rub:
            sink =avg_heigth
        #4.移動速度
        #接地力が低いほど速い
        speed = max(0.01,(2.2 - total_power)*0.5)

        #バランスペナルティ：前後の差が激しいと腰を痛める
        balance_gap = max(0,sink - h_back)
        speed -= (balance_gap * 0.5)
        
        if is_belly_rub:
            #腹這い状態：摩擦はすごいがお腹の面積で沈み込みは止まる
            speed *=0.1                      
    # バランスペナルティ（引きずり抵抗）
        drag = max(0, sink - h_back)
        # speedを直接引くのではなく、割合で減らすか下限を設ける
        speed = max(0.01, speed - (drag * 0.5))
        #水没ペナルティ
        #水面から頭が出ているか
        water_penalty = max(
            0,self.water_depth - (h_front -sink)
        )
        #骨折チャンス
        #足が長いほど、また上腕と下腕のバランスが悪いほど負荷が増える
        fronte_arm_ratio = ind.front_leg.up_leg.length /max(0.1,ind.front_leg.low_leg.length)
        #比率が1.0から離れるほど負荷倍率アップ
        structural_load = (
            ind.total_weight * (
                ind.front_leg.up_leg.length +
                  ind.front_leg.low_leg.length)
                  )*(
                      1.0 + abs(
                          1.0 - fronte_arm_ratio
                      )
                  )
        
        is_fractured = structural_load > 12.0
        #最終スコアの合算
        score = speed + (avg_heigth * 0.4) - (water_penalty*3.0) - (sink * 2.0)
        
        if is_fractured > 12.0:
            return 0.0#野生では死を意味する。
        return min(1.0,max(0.0,score))

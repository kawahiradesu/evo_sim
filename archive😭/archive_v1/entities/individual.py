# individual.py
import copy
from .parts.skeleton import Leg
from .parts.skeleton import Torso
from .parts.skeleton import Sholder
from .parts.skeleton import Pelvis
from evo_sim.archive_v1.logic.brain import Brain
import random
import math
import pygame

class Individual:
    def __init__(self, individual_id):
        self.id = individual_id
        #---2D用の属性を配置---
        #画面の真ん中ら辺にランダムに配置
        self.pos = pygame.math.Vector2(random.randint(200, 600),random.randint(200,400))
        #向いている方向
        self.angle = random.uniform(0, 360)
        #移動ベクトル
        self.velocity = pygame.math.Vector2(0, 0)
        #咀嚼タイム
        self.eat_cooldown = 0  
        #代謝の上限
        self.hydration = 1.0 #1.0で満タン,0.0で干からびる
        self.energy = 50.0
        self.eat_effect_timer = 0
        #生き物の部品
        self.gender = random.choice(["Male","Female"])
        self.front_leg = Leg()
        self.back_leg = Leg()
        self.torso = Torso()
        self.sholder = Sholder()
        self.pelvis = Pelvis()
        self.brain = Brain()
        self.update_stats()
    
    def update(self):
        #今の向きと速度で座標を少し動かす 
        self.pos += self.velocity

    def move(self, marsh):
        """
        marsh:Swampクラスのインスタンス(evaluateなどの計算用)
        """
        #自分で考える
        self.angle = self.brain.think(self,marsh)
        #既存のevaluateを流用してこの個体の「移動能力」を算出
        #evaluateの中で計算されているspeedロジックを抽出するのが理想
        current_speed = marsh.calculate_speed(self)#swamp側に計算メソッドを作っておくと楽
        #角度(self.angle)をベクトルに変換
        #pygameのVector2.from_polarを使うと、角度から「どっち方向か」がすぐに出るよ
        direction = pygame.math.Vector2(1, 0).rotate(self.angle)
        
        #速度を更新
        self.velocity = direction * current_speed
        #座標を更新
        self.pos += self.velocity
        #画面の外に出たら反対側から出てくる
        if self.pos.x > 1200: self.pos.x = 0
        if self.pos.x < 0: self.pos.x = 1200
        if self.pos.y > 800: self.pos.y = 0
        if self.pos.y < 0: self.pos.y = 800

        #代謝の仕組み
        terrain = marsh.get_terrain_at(self.pos.y)
        if terrain == "WATER":
            #水の中にいれば急速に回復
            self.hydration = min(1.0,self.hydration + 0.02)
        else :
            self.hydration -= 0.002

        self.energy -= 0.1
    
    def eat(self, marsh):
        terrain = marsh.get_terrain_at(self.pos.y)
        #捕食確率(10%の確率で捕食成功)
        if self.eat_cooldown > 0:
            self.eat_cooldown -= 1
        capture_probability = 0.05

        if random.random() < capture_probability:
            if terrain == "LAND" and marsh.insect_stock > 0:
                marsh.insect_stock -= 1
                self.energy = min(100.0, self.energy +10)#エネルギー回復
                self.eat_effect_timer = 10
                self.eat_cooldown = 20
            elif terrain =="WATER" and marsh.fish_stock > 0:
                marsh.fish_stock -= 1
                self.energy = min(100.0, self.energy + 10)
                self.eat_effect_timer = 10
                self.eat_cooldown = 20
    
    @property
    def total_weight(self):
        """個体（太郎）の全身の総重量"""
        
        # ❌ 古いコード（エラーの原因）
        # return self.torso.weight + self.front_leg.weight + self.head.weight ...
        
        # ⭕️ 新しいコード（total_weight を呼び出す）
        total = 0.0
        total += self.torso.total_weight
        total += self.front_leg.total_weight
        
        # ※ もし他にもパーツがあれば、全部 .total_weight に直すじょ！
        # total += self.back_leg.total_weight
        # total += self.head.total_weight
        # total += self.heart.base_weight  <-- 内臓(InternalPart)の場合は total_weight が無いかもしれないから base_weight にする！
        
        return total
    
    @property
    def front_body_height(self):
        """
        付け根とお腹がどれだけ浮いているのかの算出
        """
        #---肩の高さの算出---
        #1.肩の高さによる上腕の高さ
        h_up = self.front_leg.up_leg.length * math.sin(
            math.radians(self.sholder.front_join_angle * 90)
            )
        
        #膝の曲がりによる前腕の高さ
        horaizon_factor = math.cos(math.radians(
            (1.0-self.front_leg.knee_angle_horizontal)*90)
            )
        h_low = (
            self.front_leg.low_leg.length * math.sin(
                math.radians(
                    self.front_leg.knee_angle_vertical * 90)
                    )*horaizon_factor
            )

        return h_up + h_low
    
    @property
    def back_body_height(self):
        """
        付け根とお腹がどれだけ浮いているのかの算出
        """
        #---肩の高さの算出---
        #1.肩の高さによる上腕の高さ
        h_up = self.back_leg.up_leg.length * math.sin(
            math.radians(self.pelvis.hip_joint_angle * 90)
            )
        
        #膝の曲がりによる前腕の高さ
        horaizon_factor = math.cos(math.radians(
            (1.0-self.back_leg.knee_angle_horizontal)*90)
            )
        h_low = (
            self.back_leg.low_leg.length * math.sin(
                math.radians(
                    self.back_leg.knee_angle_vertical * 90)
                    )*horaizon_factor
            )

        return h_up + h_low

    def update_stats(self):
        self.protection = (self.front_leg.foot.sole.cushion + 
        self.back_leg.foot.sole.cushion)
    def inherit_from(self,parent):
        """
        親のパーツをコピーして自分のものにする。
        """
        #親のオブジェクトごと丸ごと複製して自分にセット
        self.front_leg = copy.deepcopy(parent.front_leg)
        #コピーが終わったら自分のステータスをリフレッシュ
        self.update_stats()

    def mutate(self):
        # 司令塔として、持っているパーツに変異命令を出す
        self.front_leg.mutate()
        self.back_leg.mutate()
        self.sholder.mutate()
        self.pelvis.mutate()
        self.torso.mutate()

        self.update_stats()

    def crossover(self, papa, mama):
        #骨格の遺伝
        self.torso.length = random.choice([
            papa.torso.length,
            mama.torso.length
        ])
        self.torso.width = random.choice([
            papa.torso.width,
            mama.torso.width
        ])
        self.torso.rib_cage_size = random.choice([
            papa.torso.rib_cage_size,
            mama.torso.rib_cage_size
        ])
        self.torso.flex_lateral = random.choice([
            papa.torso.flex_lateral,
            mama.torso.flex_lateral
        ])
        self.torso.flex_sagittal = random.choice([
             papa.torso.flex_sagittal,
             mama.torso.flex_sagittal
        ])
        self.sholder.scapula_size = random.choice([
            papa.sholder.scapula_size,
            mama.sholder.scapula_size
        ])
        self.sholder.clavicle_size = random.choice([
            papa.sholder.clavicle_size,
            mama.sholder.clavicle_size
        ])
        self.sholder.front_join_angle = random.choice([
            papa.sholder.front_join_angle,
            mama.sholder.front_join_angle
        ])
        self.pelvis.ilium_robustaness = random.choice([
            papa.pelvis.ilium_robustaness,
            mama.pelvis.ilium_robustaness
        ])
        self.pelvis.ischium_length = random.choice([
            papa.pelvis.ischium_length,
            mama.pelvis.ischium_length
        ])
        self.pelvis.hip_joint_angle = random.choice([
            papa.pelvis.hip_joint_angle,
            mama.pelvis.hip_joint_angle
        ])
        # --- 前脚の遺伝（上腕と前腕をそれぞれ選ぶ） ---
        self.front_leg.up_leg.length = random.choice([
            papa.front_leg.up_leg.length, 
            mama.front_leg.up_leg.length
        ])
        self.front_leg.low_leg.length = random.choice([
            papa.front_leg.low_leg.length, 
            mama.front_leg.low_leg.length
        ])
        
        # 強度なども同様に引き継ぐ
        self.front_leg.up_leg.strength = random.choice([
            papa.front_leg.up_leg.strength, 
            mama.front_leg.up_leg.strength
        ])
        # ... 以下、指の継承などはそのまま ...

        #足の裏のスタイル
        self.front_leg.foot.sole.contact_style = random.choice([
            papa.front_leg.foot.sole.contact_style, 
            mama.front_leg.foot.sole.contact_style
            ])
        self.front_leg.foot.sole.area = random.choice([
            papa.front_leg.foot.sole.area, 
            mama.front_leg.foot.sole.area
            ])

        #指の継承(指一本の単位でどちらの親に似るのか。)
        for i in range(4):
            parent_for_fingrer = random.choice([papa,mama])
            self.front_leg.foot.fingers[i] = copy.deepcopy(parent_for_fingrer.front_leg.foot.fingers[i])

        # ----後脚の遺伝（上腕と前腕をそれぞれ選ぶ） ---
        self.back_leg.up_leg.length = random.choice([
            papa.back_leg.up_leg.length, 
            mama.back_leg.up_leg.length
        ])
        self.back_leg.low_leg.length = random.choice([
            papa.back_leg.low_leg.length, 
            mama.back_leg.low_leg.length
        ])
        
        # 強度なども同様に引き継ぐ
        self.back_leg.up_leg.strength = random.choice([
            papa.back_leg.up_leg.strength, 
            mama.back_leg.up_leg.strength
        ])
        # ... 以下、指の継承などはそのまま ...

        #足の裏のスタイル
        self.back_leg.foot.sole.contact_style = random.choice([
            papa.back_leg.foot.sole.contact_style, 
            mama.back_leg.foot.sole.contact_style
            ])
        self.back_leg.foot.sole.area = random.choice([
            papa.back_leg.foot.sole.area, 
            mama.back_leg.foot.sole.area
            ])

        #指の継承(指一本の単位でどちらの親に似るのか。)
        for i in range(4):
            parent_for_fingrer = random.choice([papa,mama])
            self.back_leg.foot.fingers[i] = copy.deepcopy(parent_for_fingrer.back_leg.foot.fingers[i])
        
        self.update_stats()

    

if __name__ == "__main__":
    print("=== Individual 動作テスト開始 ===")
    test_ind = Individual(individual_id=1)
    
    print(f"初期状態のクッション: {test_ind.front_leg.foot.sole.cushion:.3f}")
    
    test_ind.mutate()
    print(f"変異後のクッション: {test_ind.front_leg.foot.sole.cushion:.3f}")
    print("=== テスト完了 ===")
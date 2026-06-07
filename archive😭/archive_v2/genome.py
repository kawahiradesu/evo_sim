import random

class Genome:
    __slot__ = ['dna']

    def __init__ (self, parent_dna = None):
        #生まれ方に関する記述
        if parent_dna:
            self.dna = self._mutate_from_parent(parent_dna)
        else:
            self.dna = self._generate_ancestor_dna()

    def _generate_ancestor_dna(self):
        """【創世記】始祖：イクチオステガの太郎モデル"""
        return {
            # --- 頭部（魚類の名残と、陸上捕食の芽生え） ---
            'skull_snout_length': 0.6, # 少し長めの顎（水中の獲物を捕らえる）
            'jaw_muscle_mass': 0.3,    # 水の抵抗があるから噛む力はまだ弱い
            'head_scale': 0.4,         # 全体的にまだ小柄
            'jaw_gape_angle': 0.7,     # 獲物を丸呑みする魚の性質を色濃く残す
               # --- 眼の構造（ハードウェア） ---
            'eye_placement': 0.5,  # 眼の位置。0.0(正面/ヒト・肉食獣) 〜 1.0(側面/ウマ・草食獣)
            'retina_density': 0.3, # 網膜の視細胞密度（暗視能力や解像度）
            'lens_focus': 0.3,     # 水晶体のピント調節能力（遠くまで見えるか）
            'optic_nerve': 0.2,    # 視神経の太さ（通信帯域＝動体視力のラグのなさ）
            'visual_cortex': 0.2,  # 視覚野の発達（脳の処理能力＝エサかゴミか判別する力）

            # 🫀 循環器系（スタミナと酸素）
            'heart_septum_dev': 0.0,  # 太郎は両生類だからまだ壁がない（0.0）
            'heart_muscle': 0.3,      # 心筋の強さ
            
            # 🥩 消化器系（何をエネルギーにできるか）
            'stomach_compartments': 0.0, # 胃の部屋の複雑さ（0.0=単胃 〜 1.0=4部屋の反芻胃）
            'stomach_acidity': 0.8,      # 胃酸の強さ（最初は肉/魚食だから強い）
            'intestine_length': 0.3,     # 腸の長さ（最初は短い）
            'cecum_size': 0.1,           # 盲腸の大きさ（最初はほぼ無い）
            
            # 🧪 代謝・肝臓（チート臓器だが燃費最悪）
            'liver_size': 0.3,           # 肝臓のデカさ
            'fat_distribution': 0.5,     # 0.0(一点集中/ラクダ) 〜 1.0(全身/アザラシ)
            
            # --- 今後追加する予定のパラメーターの妄想 ---
            # 'limb_strength': 0.2,    # 足はまだ弱く、這いつくばる程度
            # 'gill_capacity': 0.8,    # エラ呼吸メイン
            # 'lung_capacity': 0.2,    # 肺呼吸はまだ補助レベル
        }
    
    def _mutate_from_parent(self, parent_dna):
        """親のDNAをコピーしつつ、確率で揺らぎを入れる"""
        child_dna = {}
        mutation_rate = 0.05 #0.05%の確率で変異
        variance = 0.05#変異の幅

        #key, valueのペアを順に取り出している。
        for key, value in parent_dna.items():
            if random.random()<mutation_rate:
                #変異の神様のサイコロが的中
                change = value * variance
                new_value = value + random.uniform(-change, change)
                #0.0 ~ 1.0の間に収める
                child_dna[key] = max(0.0,min(1.0, new_value))

            else:
                #変異しなければそのままコピー
                child_dna[key] = value
            
        return child_dna

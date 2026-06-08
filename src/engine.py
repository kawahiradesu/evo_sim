# ==========================================
# ⚙️ engine.py：Numba爆速物理・AIエンジン（完全スペクトラム＆物理制約版）
# ==========================================
import numpy as np
# random モジュールは np.random に統一（Numba最適化のため）
from numba import njit
from config import *
from calc import *
# ------------------------------------------
# 🌿 1. 環境システム（植物とグリッド）
# ------------------------------------------
@njit
def process_plants(tree_grids, grass_grids, moisture_grids, altitude_grids, global_temperature, global_sunlight):
    """植物の成長（光獲得競争と季節変動）"""
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            m = moisture_grids[r, c]
            alt = altitude_grids[r, c]
            
            # 🌡️ 局所気温: 標高が高いほど寒い（0.0〜1.0の高度で最大-20度のペナルティ）
            local_temp = global_temperature - (alt * 20.0)
            
            # 気温が氷点下（0度以下）になると成長停止・枯死が始まる
            temp_factor = max(0.0, min(1.0, local_temp / 15.0))
            # 日照量が少ない（冬）と成長速度が落ちる
            sun_factor = global_sunlight
            
            # 総合的な成長力（水分 × 気温 × 日照量）
            growth_power = m * temp_factor * sun_factor
            
            # 🌳 木の成長（成長は遅いが、水分と温度があれば育つ）
            tree_cap = 1000.0 * m
            if tree_grids[r, c] < tree_cap:
                tree_grids[r, c] += 1.0 * growth_power
            
            # 寒すぎると木も少しずつ枯れる（冬枯れ）
            if local_temp < 0.0:
                tree_grids[r, c] += local_temp * 0.1
                if tree_grids[r, c] < 0.0: tree_grids[r, c] = 0.0
                
            # 🌿 草の成長（成長は速いが、木に光を遮られると枯れる）
            grass_cap = 1000.0 * m
            
            # 【樹冠ペナルティ】木が300を超えると日陰になり始め、600で草は完全に育たなくなる
            shade_penalty = max(0.0, min(1.0, (tree_grids[r, c] - 300.0) / 300.0))
            
            if grass_grids[r, c] < grass_cap * (1.0 - shade_penalty):
                grass_grids[r, c] += 4.0 * growth_power * (1.0 - shade_penalty)
            else:
                grass_grids[r, c] -= 2.0 # 日陰になると枯れていく
                
            # 寒すぎると草は一気に枯れる
            if local_temp < 5.0:
                grass_grids[r, c] -= (5.0 - local_temp) * 0.5
                
            if grass_grids[r, c] < 0.0: grass_grids[r, c] = 0.0

@njit
def build_grids(meat_x, meat_y, meat_active, taro_x, taro_y, taro_alive, m_counts, m_idx, t_counts, t_idx):
    """空間分割グリッドの構築（衝突判定の高速化）"""
    m_counts[:] = 0; t_counts[:] = 0
    
    for i in range(MAX_MEAT):
        if meat_active[i]:
            gx = max(0, min(int(meat_x[i] / GRID_SCALE), GRID_SIZE - 1))
            gy = max(0, min(int(meat_y[i] / GRID_SCALE), GRID_SIZE - 1))
            if m_counts[gx, gy] < 500:
                m_idx[gx, gy, m_counts[gx, gy]] = i; m_counts[gx, gy] += 1
                
    for i in range(MAX_TARO):
        if taro_alive[i]:
            gx = max(0, min(int(taro_x[i] / GRID_SCALE), GRID_SIZE - 1))
            gy = max(0, min(int(taro_y[i] / GRID_SCALE), GRID_SIZE - 1))
            if t_counts[gx, gy] < 50: 
                t_idx[gx, gy, t_counts[gx, gy]] = i; t_counts[gx, gy] += 1

# ------------------------------------------
# 🌊 1.5. 川の横断判定ヘルパー
# ------------------------------------------
@njit
def has_river_crossing(src_x, src_y, target_x, river_grids):
    """src位置からtarget_xへの移動で川を横断するかチェック"""
    gx1 = max(0, min(int(src_x / GRID_SCALE), GRID_SIZE - 1))
    gx2 = max(0, min(int(target_x / GRID_SCALE), GRID_SIZE - 1))
    gy = max(0, min(int(src_y / GRID_SCALE), GRID_SIZE - 1))
    # 自分が既に川にいる場合はペナルティなし
    if river_grids[gy, gx1] > 0.0:
        return False
    # 経路上に川があるかチェック
    start_gx = min(gx1, gx2)
    end_gx = max(gx1, gx2)
    for gx in range(start_gx, end_gx + 1):
        if river_grids[gy, gx] > 0.0:
            return True
    return False

# ------------------------------------------
# 🏃‍♂️ 2. 運動・スタミナ・物理システム
# ------------------------------------------
@njit
def update_movement_and_stamina(taro_x, taro_y, taro_alive, t_angles, t_speeds, t_current_speeds, t_sizes, t_staminas, t_max_staminas, t_lung_capas, t_muscle_ratio, t_energies, river_grids, t_fat_ratios, t_keratins, t_keratin_types, t_keratin_complexities, altitude_grids, global_temperature,t_intestine_lens):
    for i in range(len(taro_alive)):
        if not taro_alive[i]: continue

        # ⚖️ 体重ペナルティ（脂肪と鱗は重い）
        # 脂肪 + 鱗(βケラチンで単純な構造)
        mass = calc_mass(t_sizes[i], t_fat_ratios[i], t_keratins[i], t_keratin_types[i], t_keratin_complexities[i], t_intestine_lens[i])
        base_mass = t_sizes[i] ** 3
        weight_penalty = calc_weight_penalty(mass, base_mass)
        base_speed = t_speeds[i] / max(1.0, (1.0 + weight_penalty))

        # 筋肉タイプによる限界速度の決定（白筋ほど爆発力が高い）
        max_burst_speed = base_speed * (1.0 + t_muscle_ratio[i] * 2.0)
        actual_speed = min(t_current_speeds[i], max_burst_speed)

        # 息切れ判定（スタミナゼロで強制ノロノロ歩き）
        if t_staminas[i] <= 0:
            actual_speed = base_speed * 0.1 

        # ❄️ 寒冷ダメージ判定
        tx, ty = taro_x[i], taro_y[i]
        gx, gy = max(0, min(int(tx / GRID_SCALE), GRID_SIZE - 1)), max(0, min(int(ty / GRID_SCALE), GRID_SIZE - 1))
        local_temp = global_temperature - (altitude_grids[gy, gx] * 20.0)

        if local_temp < 10.0:
            # 寒冷耐性の計算: 脂肪 + 獣毛(αケラチン×単純) または ダウン(βケラチン×複雑)
            cold_resistance = calc_cold_resistance(t_fat_ratios[i], t_keratins[i], t_keratin_types[i], t_keratin_complexities[i])
            # 10度を下回った分だけ、耐性がないとダメージを受ける
            damage = (10.0 - local_temp) * (1.0 - cold_resistance) * 0.1 # 1フレームあたりのダメージ
            t_energies[i] -= damage

        # スタミナの消費と回復
        if actual_speed > base_speed * 0.3: 
            drain = (actual_speed ** 2) * t_sizes[i] * (1.0 + t_muscle_ratio[i] * 4.0) * 0.05 
            t_staminas[i] = max(0.0, t_staminas[i] - drain)
        else:
            recovery = t_lung_capas[i] * 1.5
            t_staminas[i] = min(t_staminas[i] + recovery, t_max_staminas[i])

        # 【修正前】（ワープするドーナツ世界）
        # taro_x[i] = (taro_x[i] + np.cos(t_angles[i]) * actual_speed) % WORLD_SIZE
        # taro_y[i] = (taro_y[i] + np.sin(t_angles[i]) * actual_speed) % WORLD_SIZE
        
        # 【修正後】（見えない壁に囲まれた世界）
        next_x = taro_x[i] + np.cos(t_angles[i]) * actual_speed
        next_y = taro_y[i] + np.sin(t_angles[i]) * actual_speed
        taro_x[i] = max(0.0, min(next_x, WORLD_SIZE - 0.001))
        taro_y[i] = max(0.0, min(next_y, WORLD_SIZE - 0.001))
        
        # 🌊 川の判定（river_grids から動的に取得）
        river_gx = max(0, min(int(taro_x[i] / GRID_SCALE), GRID_SIZE - 1))
        river_gy = max(0, min(int(taro_y[i] / GRID_SCALE), GRID_SIZE - 1))
        river_depth = river_grids[river_gy, river_gx]
        
        if river_depth > 0.0:
            # 川の中ではスタミナが猛烈な勢いで奪われる（深さに比例）
            t_staminas[i] -= 10.0 * river_depth
            
            # 息継ぎができずノロノロになる
            actual_speed = t_speeds[i] * 0.1 
            
            # スタミナが尽きたら直接エネルギーにダメージ（深さに比例）
            if t_staminas[i] <= 0:
                t_energies[i] -= 5.0 * river_depth
                
        # 運動器官の維持コスト（肺やタンクがデカいほど燃費悪化）
        organ_cost = (t_lung_capas[i] * 0.05) + (t_max_staminas[i] * 0.001)
        t_energies[i] -= organ_cost

# ------------------------------------------
# 🦠 3. 細菌シーソー・消化システム（脳腸相関）
# ------------------------------------------
@njit
def process_bugs(taro_x, taro_y, taro_alive, t_energies, t_true_stomach_acidities, t_microbiome, bug_grids, tree_grids, grass_grids, t_fangs):
    rows = bug_grids.shape[0]
    cols = bug_grids.shape[1]
    
    # 虫の発生（環境依存）
    for r in range(rows):
        for c in range(cols):
            tree = tree_grids[r, c]
            grass = grass_grids[r, c]
            
            # 基本は「草が多いほど虫が湧く（最大1000）」、しかし「木が多いと湧かない（減算）」
            bug_cap = (grass * 1.5) - (tree * 0.8)
            
            # 【特例】右半分（c >= 25）の砂漠は、過酷な環境に適応した「砂漠の虫」が常に湧く
            if c >= cols // 2:
                bug_cap = max(bug_cap, 500.0)
                
            bug_cap = max(0.0, bug_cap)

            if bug_grids[r, c] < bug_cap:
                bug_grids[r, c] += 10.0
                
    for i in range(len(taro_alive)):
        if not taro_alive[i]: continue
        
        grid_x, grid_y = int(taro_x[i] / GRID_SCALE), int(taro_y[i] / GRID_SCALE)
        if 0 <= grid_x < cols and 0 <= grid_y < rows:
            if bug_grids[grid_y, grid_x] > 0:
                
                # 🌟 NEW: 虫の殻を砕くには「0.5 (頑丈な円錐)」が最強！
                # 0.5のとき1.0(最高)。0.0(平ら)や1.0(ナイフ)だと 0.25(最低) になる山なり曲線
                bug_tooth_score = max(0.1, 1.0 - abs(t_fangs[i] - 0.5) * 1.5)
                
                # 胃酸と「殻砕き歯」の掛け合わせで昆虫食適正が決まる
                carni_score = t_true_stomach_acidities[i] * bug_tooth_score
               # 修正後
                eat_amount = min(bug_grids[grid_y, grid_x], 2.0 + 3.0 * carni_score)
                bug_grids[grid_y, grid_x] -= eat_amount

                # 🌟 修正：if を撤廃し、適性が低くても最低限のカロリーは吸収できるようにする
                t_energies[i] += eat_amount * 0.4 * bug_tooth_score 
                
                # 🥩 虫（肉）を食べると肉食菌方向に傾く
                # 虫食べたとき → 肉食菌方向に強く傾く
                t_microbiome[i] = max(0.0, t_microbiome[i] - eat_amount * 0.008)  # 0.002→0.008

                # 草の誤食（虫経由）→ 確率を下げる＋胃酸が強いと殺菌される
                if grass_grids[grid_y, grid_x] > 10.0:
                    accidental_plant = min(grass_grids[grid_y, grid_x], 2.0)
                    grass_grids[grid_y, grid_x] -= accidental_plant
                    acid_penalty = (1.0 - t_true_stomach_acidities[i]) ** 3
                    t_energies[i] += accidental_plant * 0.5 * acid_penalty
                    # 胃酸が強いと草食菌が胃で殺される → 転移確率が下がる
                    survival_rate = (1.0 - t_true_stomach_acidities[i]) ** 2
                    t_microbiome[i] = min(1.0, t_microbiome[i] + accidental_plant * 0.004 * survival_rate)

@njit
def update_microbiome_survival(taro_alive, t_microbiome, t_sizes, t_true_stomach_acidities, t_forestomach_capas, t_cecum_sizes):
    """臓器による細菌シーソーのパッシブ変動（壁なし）"""
    for i in range(len(taro_alive)):
        if not taro_alive[i]: continue
        
        # 物理制約：臓器は体の半分まで
        actual_forestomach = min(t_forestomach_capas[i], t_sizes[i] * 0.5)
        actual_cecum = min(t_cecum_sizes[i], t_sizes[i] * 0.5)
        
        # 胃酸(殺菌) vs シェルター(培養) の綱引き
        acid_decay = t_true_stomach_acidities[i] * 0.015 
        shelter_growth = (actual_forestomach + actual_cecum) * 0.005
        
        t_microbiome[i] += (shelter_growth - acid_decay)
        t_microbiome[i] = max(0.0, min(1.0, t_microbiome[i]))

# ------------------------------------------
# 🧠 4. AI思考システム（欲求とターゲット選択）
# ------------------------------------------
@njit
def update_ai_integrated(taro_x, taro_y, taro_alive, t_energies, t_visions, t_fangs, t_sizes, t_aggros, t_intels, t_fears, t_angles, meat_x, meat_y, meat_active, m_counts, m_idx, t_counts, t_idx, t_true_stomach_acidities, t_forestomach_capas, t_intestine_lens, t_microbiome, grass_grids, t_speeds, t_current_speeds, river_grids, t_keratins, t_nerve_densities):
    for i in range(len(taro_alive)):
        if not taro_alive[i]: continue
        tx, ty = taro_x[i], taro_y[i]
        gx, gy = max(0, min(int(tx / GRID_SCALE), GRID_SIZE - 1)), max(0, min(int(ty / GRID_SCALE), GRID_SIZE - 1))
        
        # 📡 感覚毛（Sensory Hair）による知覚ボーナス
        sensory_score = t_keratins[i] * t_nerve_densities[i]
        # 森の中(tree_grids)などの視界ペナルティはまだ実装していないが、
        # ここでは常に視界に最大1.5倍のボーナスがかかるようにする
        actual_vision = t_visions[i] * (1.0 + sensory_score * 0.5)

        best_score = -1.0; best_x = -1.0; best_y = -1.0
        
        # 細菌シーソーがAIの欲求をハックする
        # 食欲は「細菌のシーソー」だけに支配される（脳腸相関）
        actual_herb_score = t_microbiome[i]         # 草食菌が多いほど草を求める
        actual_scavenge_score = 1.0 - t_microbiome[i] # 肉食菌が多いほど死肉を求める
        
        # 殺意は「闘争心」のみ。マーダーヴィーガン大歓迎！
        killer_score = t_aggros[i]

        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    
                    # 🌿 草の評価
                    plant_amount = grass_grids[ny, nx]
                    if plant_amount > 50.0:
                        grid_center_x = nx * GRID_SCALE + (GRID_SCALE / 2.0)
                        grid_center_y = ny * GRID_SCALE + (GRID_SCALE / 2.0)
                        dist = np.sqrt((grid_center_x - tx)**2 + (grid_center_y - ty)**2)
                        if 0 < dist < actual_vision:
                            score = actual_herb_score * (plant_amount / 500.0) * (1.0 - dist / actual_vision) * 150.0
                            # 🌊 川越えペナルティ（river_grids参照）
                            if has_river_crossing(tx, ty, grid_center_x, river_grids):
                                score *= 0.01
                            if score > best_score:
                                best_score, best_x, best_y = score, grid_center_x, grid_center_y
                    
                    # 🍖 死肉の評価
                    for c in range(m_counts[nx, ny]):
                        idx = m_idx[nx, ny, c]
                        if meat_active[idx]:
                            dist = np.sqrt((meat_x[idx] - tx)**2 + (meat_y[idx] - ty)**2)
                            if 0 < dist < actual_vision:
                                # actual_scavenge_score を使用
                                score = actual_scavenge_score * (1.0 - dist / actual_vision) * 100.0
                                # 🌊 川越えペナルティ（river_grids参照）
                                if has_river_crossing(tx, ty, meat_x[idx], river_grids):
                                    score *= 0.01
                                
                                if score > best_score:
                                    best_score, best_x, best_y = score, meat_x[idx], meat_y[idx]

                    # ⚔️ 他の太郎の評価（恐怖と狩猟）
                    for c in range(t_counts[nx, ny]):
                        idx = t_idx[nx, ny, c]
                        if idx == i or not taro_alive[idx]: continue
                        dist = np.sqrt((taro_x[idx] - tx)**2 + (taro_y[idx] - ty)**2)
                        
                        noise_level = t_current_speeds[idx] / (t_speeds[idx] + 0.001) 
                        effective_vision = actual_vision * (0.2 + noise_level * 0.8)
                        
                        if 0 < dist < effective_vision:
                            current_fear = (t_sizes[idx] / t_sizes[i]) * t_fears[i]
                            if current_fear > 1.0 and t_aggros[idx] > 0.3:
                                fear_score = ((t_intels[i] + 0.5) * 300.0 * current_fear) / (dist + 1.0)
                                if fear_score > best_score:
                                    best_score, best_x, best_y = fear_score, tx + (tx - taro_x[idx]), ty + (ty - taro_y[idx])
                            
                            elif t_sizes[i] > t_sizes[idx] * 0.9:
                                birth_threshold_i = (200.0 + (t_sizes[i] * 150.0)) * 1.2
                                if t_energies[i] < birth_threshold_i:
                                    # 飢えていれば「エサ」として襲う
                                    hunt_score = killer_score * (1.0 - dist / actual_vision) * 200.0
                                    # 🌊 狩猟時の川越えペナルティ（river_grids参照）
                                    if has_river_crossing(tx, ty, taro_x[idx], river_grids):
                                        hunt_score *= 0.01
                                    if hunt_score > best_score:
                                        best_score, best_x, best_y = hunt_score, taro_x[idx], taro_y[idx]
                                elif killer_score > 0.8 and dist < 2.0:
                                    # 飢えていなくても、キレやすければ単なる殺意で襲う（マーダーヴィーガン発動）
                                    combat_score = (killer_score * 200.0) / (dist + 1.0)
                                    if has_river_crossing(tx, ty, taro_x[idx], river_grids):
                                        combat_score *= 0.01
                                    if combat_score > best_score:
                                        best_score, best_x, best_y = combat_score, taro_x[idx], taro_y[idx]

        if best_score > 0: 
            t_angles[i] = np.arctan2(best_y - ty, best_x - tx)
            dist_to_target = np.sqrt((best_x - tx)**2 + (best_y - ty)**2)
            burst_range = t_speeds[i] * 2.0 
            
            if dist_to_target < burst_range:
                t_current_speeds[i] = t_speeds[i] * 3.0 # 強襲フェーズ
            else:
                stealth_factor = max(0.2, 1.0 - t_intels[i]) 
                t_current_speeds[i] = t_speeds[i] * stealth_factor # 隠密フェーズ
        else: 
            t_angles[i] += (np.random.random() * 0.4 - 0.2)
            t_current_speeds[i] = t_speeds[i] * 0.3 # 徘徊フェーズ
            # 🌊 川の手前（警告ゾーン）で岸の方向へターンさせる（river_grids参照）
            wander_gx = max(0, min(int(tx / GRID_SCALE), GRID_SIZE - 1))
            wander_gy = max(0, min(int(ty / GRID_SCALE), GRID_SIZE - 1))
            if river_grids[wander_gy, wander_gx] == 0.0:
                for check_d in range(1, 3):
                    r_gx = wander_gx + check_d
                    if 0 <= r_gx < GRID_SIZE and river_grids[wander_gy, r_gx] > 0.0:
                        t_angles[i] = np.pi  # 右に川→左に逃げる
                        break
                    l_gx = wander_gx - check_d
                    if 0 <= l_gx < GRID_SIZE and river_grids[wander_gy, l_gx] > 0.0:
                        t_angles[i] = 0.0  # 左に川→右に逃げる
                        break
# ------------------------------------------
# 💞 5. 遺伝・交配・戦闘システム
# ------------------------------------------
@njit
def get_genetic_distance(i, j, t_fangs, t_sizes, t_speeds, t_aggros, t_intels, t_true_stomach_acidities, t_forestomach_capas, t_intestine_lens, t_cecum_sizes):
    # 全遺伝子距離（繁殖互換性の判定に使用）
    D_sq = ((t_fangs[i] - t_fangs[j])**2 + ((t_sizes[i] - t_sizes[j]) / 3.0)**2 + ((t_speeds[i] - t_speeds[j]) / 4.0)**2 +
            (t_aggros[i] - t_aggros[j])**2 + (t_intels[i] - t_intels[j])**2 + (t_true_stomach_acidities[i] - t_true_stomach_acidities[j])**2 +
            (t_forestomach_capas[i] - t_forestomach_capas[j])**2 + (t_intestine_lens[i] - t_intestine_lens[j])**2 + (t_cecum_sizes[i] - t_cecum_sizes[j])**2)
    return D_sq ** 0.5

@njit
def get_morpho_distance(i, j, t_fangs, t_sizes, t_intestine_lens, t_true_stomach_acidities):
    # 形態的距離（同種判定に使用）
    # 生物学的根拠: 種の同一性は行動形質(aggros/intels/fears)ではなく
    # 体の構造(牙・サイズ・消化器官)で決まる。黒人と白人が同種なのと同じ。
    D_sq = ((t_fangs[i] - t_fangs[j])**2 +
            (t_sizes[i] - t_sizes[j])**2 +
            (t_intestine_lens[i] - t_intestine_lens[j])**2 +
            (t_true_stomach_acidities[i] - t_true_stomach_acidities[j])**2)
    return D_sq ** 0.5

@njit
def attempt_mating(i, j, tx, ty, taro_alive, taro_x, taro_y, t_energies, t_fangs, t_sizes, t_speeds, t_aggros, t_intels, t_visions, t_true_stomach_acidities, t_forestomach_capas, t_intestine_lens, t_cecum_sizes, t_fears, t_ages, t_microbiome, t_max_staminas, t_lung_capas, t_muscle_ratio, t_staminas, t_cooldowns, t_metabolisms, t_fat_ratios, t_keratins, t_keratin_types, t_keratin_complexities, t_nerve_densities):
    
    # 🌟 NEW: 性成熟は「体のサイズ」に比例する！（小さいほど早熟）
    maturity_i = int(200.0 * t_sizes[i])
    maturity_j = int(200.0 * t_sizes[j])
    
    if t_ages[i] < maturity_i or t_cooldowns[i] > 0: return False
    if t_ages[j] < maturity_j or t_cooldowns[j] > 0: return False

    birth_threshold_i = 200.0 + (t_sizes[i] * 100.0)
    birth_threshold_j = 200.0 + (t_sizes[j] * 100.0)
    breed_req_i = birth_threshold_i  # * 1.5 を削除
    breed_req_j = birth_threshold_j


    if t_energies[i] > breed_req_i and t_energies[j] > breed_req_j:
        child_idx = -1
        for k in range(len(taro_alive)):
            if not taro_alive[k]: 
                child_idx = k; break
                
        if child_idx != -1:
            tax = 50.0
            pool = (t_energies[i] + t_energies[j]) - tax 
            t_energies[i] = min(pool * 0.25, birth_threshold_i * 0.8)
            t_energies[j] = min(pool * 0.25, birth_threshold_j * 0.8)
            
            # 🌟 NEW: オスとメスの役割分担 ＆ r/K選択説
            # i を「母（妊娠してエネルギーを消費する側）」、j を「父」と見立てる
            pregnancy_time = int(200.0 * t_sizes[i])  # 400→200
            t_cooldowns[i] = pregnancy_time
            t_cooldowns[j] = 30  # 50→30
            
            # --- 子の基本ステータス初期化（1回だけ！） ---
            taro_alive[child_idx] = True
            t_ages[child_idx] = 0
            t_cooldowns[child_idx] = 0
            # 親の近くに生まれる（壁を突き抜けないよう max/min でクランプ）
            taro_x[child_idx] = max(0.0, min(tx + np.random.uniform(-2.0, 2.0), WORLD_SIZE - 0.001))
            taro_y[child_idx] = max(0.0, min(ty + np.random.uniform(-2.0, 2.0), WORLD_SIZE - 0.001))
            t_energies[child_idx] = pool * 0.50

            # DNAブレンド（ガウス変異ベース）
            # 牙 (Fangs)
            base_fang = t_fangs[i] if np.random.random() < 0.5 else t_fangs[j]
            t_fangs[child_idx] = max(0.0, min(1.0, base_fang + np.random.normal(0, 0.05)))
            
            # サイズ (Sizes)
            base_size = t_sizes[i] if np.random.random() < 0.5 else t_sizes[j]
            t_sizes[child_idx] = max(0.5, min(3.0, base_size + np.random.normal(0, 0.1)))
            
            # スピード (Speeds)
            base_speed = t_speeds[i] if np.random.random() < 0.5 else t_speeds[j]
            t_speeds[child_idx] = max(0.5, min(4.0, base_speed + np.random.normal(0, 0.1)))
            
            # 闘争心 (Aggros)
            base_aggro = t_aggros[i] if np.random.random() < 0.5 else t_aggros[j]
            t_aggros[child_idx] = max(0.0, min(1.0, base_aggro + np.random.normal(0, 0.05)))
            
            # 知能と恐怖 (Intels & Fears)
            base_intel = t_intels[i] if np.random.random() < 0.5 else t_intels[j]
            t_intels[child_idx] = max(0.0, min(1.0, base_intel + np.random.normal(0, 0.05)))
            base_fear = t_fears[i] if np.random.random() < 0.5 else t_fears[j]
            t_fears[child_idx] = max(0.0, min(1.0, base_fear + np.random.normal(0, 0.05)))
            
            # 視界 (Visions) — 他の形質と同様に遺伝＋変異させる
            base_vision = t_visions[i] if np.random.random() < 0.5 else t_visions[j]
            t_visions[child_idx] = max(3.0, min(30.0, base_vision + np.random.normal(0, 1.0)))
            
            # 消化器官 (Organs) - まとめて遺伝する確率も持たせるとよりリアルですが、今回は独立交叉
            base_acid = t_true_stomach_acidities[i] if np.random.random() < 0.5 else t_true_stomach_acidities[j]
            t_true_stomach_acidities[child_idx] = max(0.0, min(1.0, base_acid + np.random.normal(0, 0.05)))
            
            base_intestine = t_intestine_lens[i] if np.random.random() < 0.5 else t_intestine_lens[j]
            t_intestine_lens[child_idx] = max(0.0, min(1.0, base_intestine + np.random.normal(0, 0.05)))
            
            base_fore = t_forestomach_capas[i] if np.random.random() < 0.5 else t_forestomach_capas[j]
            t_forestomach_capas[child_idx] = max(0.0, min(1.0, base_fore + np.random.normal(0, 0.05)))
            
            base_cecum = t_cecum_sizes[i] if np.random.random() < 0.5 else t_cecum_sizes[j]
            t_cecum_sizes[child_idx] = max(0.0, min(1.0, base_cecum + np.random.normal(0, 0.05)))
            
            # スタミナ・運動系
            base_max_stam = t_max_staminas[i] if np.random.random() < 0.5 else t_max_staminas[j]
            t_max_staminas[child_idx] = max(10.0, base_max_stam + np.random.normal(0, 10.0))
            
            base_lung = t_lung_capas[i] if np.random.random() < 0.5 else t_lung_capas[j]
            t_lung_capas[child_idx] = max(0.05, min(1.5, base_lung + np.random.normal(0, 0.05)))
            
            base_muscle = t_muscle_ratio[i] if np.random.random() < 0.5 else t_muscle_ratio[j]
            t_muscle_ratio[child_idx] = max(0.0, min(1.0, base_muscle + np.random.normal(0, 0.05)))
            
            t_staminas[child_idx] = t_max_staminas[child_idx]
            
            # 細菌（腸内環境は親から子へそのまま受け継ぐが、少し揺らぐ）
            acid_filter = 1.0 - t_true_stomach_acidities[child_idx] * 0.5
            base_micro = t_microbiome[i] if np.random.random() < 0.5 else t_microbiome[j]
            t_microbiome[child_idx] = max(0.0, min(1.0, base_micro * acid_filter + np.random.uniform(-0.05, 0.05)))
            
            # 🧬 NEW: 環境適応・体表遺伝子
            t_metabolisms[child_idx] = max(0.0, min(1.0, (t_metabolisms[i] if np.random.random() < 0.5 else t_metabolisms[j]) + np.random.normal(0, 0.05)))
            t_fat_ratios[child_idx] = max(0.0, min(1.0, (t_fat_ratios[i] if np.random.random() < 0.5 else t_fat_ratios[j]) + np.random.normal(0, 0.05)))
            t_keratins[child_idx] = max(0.0, min(1.0, (t_keratins[i] if np.random.random() < 0.5 else t_keratins[j]) + np.random.normal(0, 0.05)))
            
            # α/βケラチンの系統制約（タイプは突然変異しにくい、0か1かに寄せる）
            base_type = t_keratin_types[i] if np.random.random() < 0.5 else t_keratin_types[j]
            if np.random.random() < 0.01: base_type = 1.0 - base_type # 1%の確率で系統反転
            t_keratin_types[child_idx] = base_type
            
            t_keratin_complexities[child_idx] = max(0.0, min(1.0, (t_keratin_complexities[i] if np.random.random() < 0.5 else t_keratin_complexities[j]) + np.random.normal(0, 0.05)))
            t_nerve_densities[child_idx] = max(0.0, min(1.0, (t_nerve_densities[i] if np.random.random() < 0.5 else t_nerve_densities[j]) + np.random.normal(0, 0.05)))
            
            return True
    return False

@njit
def attempt_combat(i, j, is_same_species, meat_efficiency, taro_alive, taro_x, taro_y, t_energies, t_fangs, t_sizes, t_aggros, t_forestomach_capas, t_cecum_sizes, t_ages, death_stats, t_staminas, t_max_staminas, t_muscle_ratio, meat_x, meat_y, meat_amount, meat_active, meat_age, t_keratins, t_keratin_types, t_keratin_complexities):
    attack_cost = 10.0 * (1.0 + t_muscle_ratio[i] * 2.0)
    t_staminas[i] = max(0.0, t_staminas[i] - attack_cost)
    defense_cost = 5.0 * (1.0 + t_muscle_ratio[j] * 2.0)
    t_staminas[j] = max(0.0, t_staminas[j] - defense_cost)
    
    fatigue_ratio_j = max(0.0, (t_staminas[j] / (t_max_staminas[j] + 0.001)) - 0.5) * 2.0

    # 🛡️ 防御側(j)の物理防御力を計算: βケラチン × 単純構造(鱗)
    armor_value_j = calc_armor_value(t_keratins[j], t_keratin_types[j], t_keratin_complexities[j], t_sizes[j])
    damage_multiplier_j = calc_damage_multiplier(armor_value_j)

    if is_same_species:
        # 共食いバイアス（飢えと闘争心に依存）
        if np.random.random() < t_aggros[i] and t_energies[i] < 100.0:
            recoil = (t_fangs[j] ** 2) * t_sizes[j] * 30.0 * fatigue_ratio_j
            t_energies[i] -= recoil

            if t_energies[i] <= 0:
                taro_alive[i] = False; death_stats[2] += 1; return True
            
            damage = (t_fangs[i] ** 2) * t_sizes[i] * 50.0 * damage_multiplier_j
            t_energies[j] -= damage
            if t_energies[j] <= 0:
                taro_alive[j] = False; death_stats[2] += 1; death_stats[3] += t_ages[j]
                for m in range(len(meat_active)):
                    if not meat_active[m]:
                        meat_active[m] = True; meat_x[m] = taro_x[j]; meat_y[m] = taro_y[j]
                        meat_amount[m] = t_sizes[j] * 50.0; meat_age[m] = 0; break
            return True
            
    else:
        # 🌟 狩猟バイアス（if t_fangs > 0.4 を撤廃！すべては闘争心と確率）
        if np.random.random() < t_aggros[i]:
            hunter_lightness = 2.0 - (t_forestomach_capas[i] + t_cecum_sizes[i])
            recoil = t_sizes[j] * 10.0
            if t_fangs[j] > 0.2:
                recoil += (t_fangs[j] ** 2) * t_sizes[j] * 20.0
            
            t_energies[i] -= (recoil * fatigue_ratio_j)
            if t_energies[i] <= 0:
                taro_alive[i] = False; death_stats[2] += 1; death_stats[3] += t_ages[i]; return True

            # 牙が丸い(0.1など)とダメージはほぼ出ない（物理的制約）
            damage = (t_fangs[i] ** 2) * t_sizes[i] * hunter_lightness * 150.0 * damage_multiplier_j
            t_energies[j] -= damage
            if t_energies[j] <= 0:
                taro_alive[j] = False; death_stats[2] += 1; death_stats[3] += t_ages[j]
                for m in range(len(meat_active)):
                    if not meat_active[m]:
                        meat_active[m] = True; meat_x[m] = taro_x[j]; meat_y[m] = taro_y[j]
                        meat_amount[m] = t_sizes[j] * 100.0; meat_age[m] = 0; break
            return True
    return False

# ------------------------------------------
# 🥩 6. 食事・相互作用システム
# ------------------------------------------
@njit
def process_interactions(taro_x, taro_y, taro_alive, t_energies, t_fangs, t_sizes, t_true_stomach_acidities, t_forestomach_capas, t_intestine_lens, t_cecum_sizes, t_speeds, t_visions, t_aggros, t_intels, t_fears, meat_x, meat_y, meat_amount, meat_active, m_counts, m_idx, t_counts, t_idx, t_ages, t_microbiome, grass_grids, death_stats, t_max_staminas, t_lung_capas, t_muscle_ratio, t_staminas, meat_age, t_cooldowns, t_metabolisms, t_fat_ratios, t_keratins, t_keratin_types, t_keratin_complexities, t_nerve_densities):
    eat_dist_sq = 2.0 * 2.0
    interact_dist_sq = 3.0 * 3.0

    for i in range(len(taro_alive)):
        if not taro_alive[i]: continue
        tx, ty = taro_x[i], taro_y[i]
        gx, gy = max(0, min(int(tx / GRID_SCALE), GRID_SIZE - 1)), max(0, min(int(ty / GRID_SCALE), GRID_SIZE - 1))
        acted = False

        # 臓器サイズの物理制約を適用して消化効率を事前計算
        actual_forestomach = min(t_forestomach_capas[i], t_sizes[i] * 0.5)
        actual_cecum = min(t_cecum_sizes[i], t_sizes[i] * 0.5)

        # 🌿 草の消化効率
        grass_organ_score = (actual_forestomach + actual_cecum + t_intestine_lens[i]) / 3.0
        # 🌟 FIX: 草のペナルティを線形に（0.0で100%効率、0.5で50%効率、1.0でほぼ0%）
        grass_penalty = max(0.01, 1.0 - t_fangs[i]) 
        grass_efficiency = grass_organ_score * grass_penalty
        
        # 🍖 肉の消化効率
        meat_organ_score = t_true_stomach_acidities[i] * (1.1 - t_intestine_lens[i]) * (1.1 - actual_forestomach)
        # 🌟 そのまま: 肉のボーナスは二次曲線（0.5では25%効率で鈍いが、1.0で100%効率のナイフになる）
        meat_efficiency = meat_organ_score * max(0.01, t_fangs[i] ** 2) * (3.0 + (t_fangs[i] * 3.0))

        for dx in range(-1, 2):
            if acted: break
            for dy in range(-1, 2):
                if acted: break
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    
                    # ⚔️ 太郎同士の接触判定
                    for c in range(t_counts[nx, ny]):
                        j = t_idx[nx, ny, c]
                        if i != j and taro_alive[j] and taro_alive[i] and (taro_x[j] - tx)**2 + (taro_y[j] - ty)**2 < interact_dist_sq:
                            D = get_genetic_distance(i, j, t_fangs, t_sizes, t_speeds, t_aggros, t_intels, t_true_stomach_acidities, t_forestomach_capas, t_intestine_lens, t_cecum_sizes)
                            M = get_morpho_distance(i, j, t_fangs, t_sizes, t_intestine_lens, t_true_stomach_acidities)
                            
                            # 繁殖: 全遺伝子距離が近ければOK
                            if D < 0.4:
                               acted = attempt_mating(i, j, tx, ty, taro_alive, taro_x, taro_y, t_energies, t_fangs, t_sizes, t_speeds, t_aggros, t_intels, t_visions, t_true_stomach_acidities, t_forestomach_capas, t_intestine_lens, t_cecum_sizes, t_fears, t_ages, t_microbiome, t_max_staminas, t_lung_capas, t_muscle_ratio, t_staminas, t_cooldowns, t_metabolisms, t_fat_ratios, t_keratins, t_keratin_types, t_keratin_complexities, t_nerve_densities)
                            if not acted:
                               # 同種判定: 形態的距離で判断（行動形質は無視）
                               acted = attempt_combat(i, j, (M < 0.4), meat_efficiency, taro_alive, taro_x, taro_y, t_energies, t_fangs, t_sizes, t_aggros, t_forestomach_capas, t_cecum_sizes, t_ages, death_stats, t_staminas, t_max_staminas, t_muscle_ratio, meat_x, meat_y, meat_amount, meat_active, meat_age, t_keratins, t_keratin_types, t_keratin_complexities)
                            if acted: break
                    if acted: break
                    
                    # 🌿 草を食べる処理（確率バイアス）
                    herb_bias = t_microbiome[i]
                    if np.random.random() < herb_bias + 0.02:
                        if grass_grids[ny, nx] > 20.0:
                            eat_amount = min(grass_grids[ny, nx], 20.0)
                            grass_grids[ny, nx] -= eat_amount
                            
                            acid_penalty = (1.0 - t_true_stomach_acidities[i]) ** 3
                            base_digestion = eat_amount * grass_efficiency * acid_penalty
                            fermentation_bonus = eat_amount * t_microbiome[i] * 1.5
                            t_energies[i] += (base_digestion + fermentation_bonus)
                            
                            # 🦠 生物学的根拠: 胃酸が強いと摂取した植物由来の草食菌が胃で殺菌される。
                            # 草食寄り個体(低胃酸)ほど細菌が定着しやすく、肉食個体はほぼ定着しない。
                            acid_survival = (1.0 - t_true_stomach_acidities[i]) ** 2
                            t_microbiome[i] = min(1.0, t_microbiome[i] + eat_amount * 0.01 * acid_survival)
                            acted = True; break

                    # 🍖 地面の肉を食べる処理（🌟 牙の壁を撤廃し、確率バイアス化！）
                    meat_bias = 1.0 - t_microbiome[i]
                    if np.random.random() < meat_bias + 0.02:
                        for c in range(m_counts[nx, ny]):
                            idx = m_idx[nx, ny, c]
                            if meat_active[idx] and (meat_x[idx] - tx)**2 + (meat_y[idx] - ty)**2 < eat_dist_sq:
                                eat_amount = min(50.0, meat_amount[idx])
                                meat_amount[idx] -= eat_amount
                                
                                rot_level = min(1.0, meat_age[idx] / 200.0)
                                poison_resist = min(1.0, (actual_cecum * 5.0) + (t_true_stomach_acidities[i] * 0.6))
                                toxicity = rot_level * max(0.0, 1.0 - poison_resist)
                                
                                if toxicity > 0.4:
                                    t_energies[i] -= eat_amount * toxicity * 2.0
                                else:
                                    nutrition_loss = 1.0 - (rot_level * 0.5)
                                    t_energies[i] += eat_amount * meat_efficiency * nutrition_loss
                                
                                # 🦠 生物学的根拠: 肉食により腸内環境が酸性・嫌気性になり草食菌が死滅する
                                t_microbiome[i] = max(0.0, t_microbiome[i] - eat_amount * 0.008)  # 0.005→0.008
                                acted = True
                                if meat_amount[idx] <= 0: meat_active[idx] = False
                                break

# ------------------------------------------
# ⏳ 7. 寿命・腐敗システム
# ------------------------------------------
@njit
def process_life_cycle(taro_x, taro_y, taro_alive, t_energies, t_speeds, t_visions, t_fangs, t_sizes, t_aggros, t_intels, t_true_stomach_acidities, t_forestomach_capas, t_intestine_lens, t_cecum_sizes, meat_x, meat_y, meat_amount, meat_active, t_ages, death_stats, meat_age, t_cooldowns, t_metabolisms, t_keratins, t_nerve_densities):
    BASE_LIFESPAN = 4000 
    for i in range(len(taro_alive)):
        if not taro_alive[i]: continue
        t_ages[i] += 1

        # 🌟 NEW: クールダウンを毎フレーム減らす
        if t_cooldowns[i] > 0:
            t_cooldowns[i] -= 1

        lifespan = BASE_LIFESPAN * (t_sizes[i] * 0.5 + 0.5) 
        if t_ages[i] > lifespan:
            taro_alive[i] = False
            death_stats[0] += 1
            death_stats[3] += t_ages[i]
            for m in range(len(meat_active)):
                if not meat_active[m]:
                    meat_active[m] = True; meat_x[m] = taro_x[i]; meat_y[m] = taro_y[i]
                    meat_amount[m] = t_sizes[i] * 100.0; meat_age[m] = 0; break 
            continue 
        
        # 物理サイズに基づいた維持コスト
        actual_forestomach = min(t_forestomach_capas[i], t_sizes[i] * 0.5)
        actual_cecum = min(t_cecum_sizes[i], t_sizes[i] * 0.5)
        organ_cost = (actual_forestomach * 0.1) + (actual_cecum * 0.08) + (t_intestine_lens[i] * 0.05) + (t_true_stomach_acidities[i] * 0.02)
        
        # 🧬 NEW: 環境適応遺伝子による維持コスト
        # ケラチン維持コスト（量に比例）
        keratin_cost = t_keratins[i] * 0.1 * t_sizes[i]
        # 神経維持コスト（感覚毛）
        nerve_cost = t_nerve_densities[i] * t_keratins[i] * 0.2 * t_sizes[i]
        
        # 基礎代謝(metabolisms)が高いと全てにおいて消費が激しいが、ベースコストも上がる
        base_cost = 0.1 + ((t_sizes[i] ** 2) * 0.15) + (t_speeds[i] * 0.05) + organ_cost * 0.5 + keratin_cost + nerve_cost
        metabolism_multiplier = 0.5 + t_metabolisms[i] # 0.5 ~ 1.5 倍
        
        t_energies[i] -= (base_cost * metabolism_multiplier)
        if t_energies[i] <= 0:
            taro_alive[i] = False
            death_stats[1] += 1
            death_stats[3] += t_ages[i]
            for m in range(len(meat_active)):
                if not meat_active[m]:
                    meat_active[m] = True; meat_x[m] = taro_x[i]; meat_y[m] = taro_y[i]; meat_amount[m] = 10.0; meat_age[m] = 0; break

@njit
def process_meat_decay(meat_amount, meat_active, meat_age):
    """肉の腐敗と消滅"""
    for i in range(len(meat_active)):
        if meat_active[i]:
            meat_age[i] += 1
            meat_amount[i] -= 0.2
            if meat_amount[i] < 1.0: meat_active[i] = False
@njit
def debug_energy_trace(taro_alive, t_energies, t_sizes, t_speeds, t_ages, frame_count, interval=1000):
    """DEBUG: エネルギー収支を定期出力"""
    if frame_count % interval != 0:
        return
    
    alive_idx = np.where(taro_alive)[0]
    if len(alive_idx) == 0:
        print(f"Frame {frame_count}: 全員死亡")
        return
    
    energies = t_energies[alive_idx]
    print(f"Frame {frame_count}:")
    print(f"  生存数: {len(alive_idx)}")
    print("  エネルギー: min=", energies.min(), " max=", energies.max(), " mean=", energies.mean())
# ------------------------------------------
# 📦 8. 通信・描画用データ抽出システム
# ------------------------------------------
@njit
def extract_active_coords(x, y, active_flag, out_buffer):
    idx = 0
    for i in range(len(active_flag)):
        if active_flag[i]:
            out_buffer[idx] = x[i]; out_buffer[idx+1] = y[i]; idx += 2
    return idx

@njit
def extract_taro_render_data(taro_x, taro_y, taro_alive, t_speeds, t_visions, t_fangs, t_sizes, t_true_stomach_acidities, t_intestine_lens, buffer_taro):
    count = 0
    for i in range(MAX_TARO): 
        if taro_alive[i]:
            buffer_taro[count * 8 + 0] = taro_x[i]
            buffer_taro[count * 8 + 1] = taro_y[i]
            buffer_taro[count * 8 + 2] = t_true_stomach_acidities[i]
            buffer_taro[count * 8 + 3] = t_sizes[i]
            buffer_taro[count * 8 + 4] = t_speeds[i]
            buffer_taro[count * 8 + 5] = t_fangs[i]          
            buffer_taro[count * 8 + 6] = t_intestine_lens[i] 
            buffer_taro[count * 8 + 7] = 0.2                 
            count += 1
    return count * 8

@njit
def extract_plant_render_data(tree_grids, grass_grids, buffer_plants):
    """木と草の2つのデータをフロントエンドに送る"""
    idx = 0
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            buffer_plants[idx] = tree_grids[r, c]
            buffer_plants[idx+1] = grass_grids[r, c]
            idx += 2
    return idx
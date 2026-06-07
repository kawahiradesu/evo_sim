# ==========================================
# 📐 calc.py：数値計算層（純粋関数）
# ==========================================
# 設計原則：
#   - 全関数が @njit（Numba JIT対象）
#   - 引数だけを受け取り、数値を返す
#   - 配列への書き込みなし（副作用なし）
#   - engine.py のロジック層から呼び出される
#
# 単位系：
#   - t_sizes : m（1.0 = イクチオステガ基準、体長1m）
#   - energy  : 任意単位（相対値）
#   - 0.0〜1.0 の形質はすべて正規化済み比率値
# ==========================================

import numpy as np
from numba import njit
from src.config import *


# ------------------------------------------
# ⚖️ 質量・体重系
# ------------------------------------------

@njit
def calc_mass(size, fat_ratio, keratin, keratin_type, keratin_complexity, intestine_len):
    """
    個体の総質量を返す（size=1.0 = イクチオステガ基準）

    設計メモ：
      - base_mass = size^3（体積は辺長の3乗に比例）
      - scale_density：βケラチン × 単純構造 → 鱗（重い）
      - fur_density  ：αケラチン → 毛（軽い）
      - 将来拡張：osteoderms（骨皮）, feather_density（羽毛）を引数追加で対応予定
    """
    base_mass = size ** 3

    # ケラチン形質から表皮タイプを導出
    scale_density = keratin * keratin_type * (1.0 - keratin_complexity)   # 鱗成分
    fur_density   = keratin * (1.0 - keratin_type)                        # 毛成分

    scale_weight    = scale_density * (keratin_type * (1.0 - keratin_complexity)) * 0.6
    fat_weight      = fat_ratio * 0.3
    intestine_weight = intestine_len * 0.2
    filament_weight = fur_density * 0.05

    mass = base_mass * (1.0 + scale_weight + fat_weight + intestine_weight + filament_weight)
    return mass


@njit
def calc_weight_penalty(mass, base_mass):
    """
    速度補正用の重さペナルティ（0.0〜1.0）
    mass / (mass + base_mass) で正規化
    デフォルト個体（イクチオステガ）で約0.50
    """
    return mass / (mass + base_mass)


# ------------------------------------------
# 🌿 消化・栄養吸収系
# ------------------------------------------

@njit
def calc_actual_organ_size(organ_capa, size):
    """
    物理制約：臓器は体の半分までしか入らない
    engine.py 全体で繰り返し使われる計算を統一
    """
    return min(organ_capa, size * 0.5)


@njit
def calc_grass_efficiency(actual_forestomach, actual_cecum, intestine_len, fangs):
    """
    草の消化効率（0.0〜1.0）
    臓器スコア × 牙ペナルティ（牙が鋭いほど草を食べにくい）
    """
    grass_organ_score = (actual_forestomach + actual_cecum + intestine_len) / 3.0
    grass_penalty     = max(0.01, 1.0 - fangs)
    return grass_organ_score * grass_penalty


@njit
def calc_fermentation_bonus(eat_amount, microbiome, actual_forestomach, actual_cecum):
    """
    発酵ボーナス（腸内細菌による草からの追加エネルギー）

    設計メモ：
      - microbiome は「菌の傾き（比率）」であり絶対量ではない
      - actual_forestomach + actual_cecum が「菌の住める家の広さ」
      - 臓器なしでは菌が定着できないため発酵は起きない
      - 臓器を獲得してから菌が定着するまでタイムラグが生まれる（生物学的に正しい）
    """
    housing_capacity = actual_forestomach + actual_cecum
    effective_microbiome = microbiome * housing_capacity
    return eat_amount * effective_microbiome * 3.0


@njit
def calc_meat_efficiency(true_stomach_acidity, intestine_len, actual_forestomach, fangs):
    """
    肉の消化効率
    胃酸 × 短腸ボーナス × 牙の鋭さ（二次曲線）
    """
    meat_organ_score = true_stomach_acidity * (1.1 - intestine_len) * (1.1 - actual_forestomach)
    return meat_organ_score * max(0.01, fangs ** 2) * (3.0 + (fangs * 3.0))


@njit
def calc_acid_penalty(true_stomach_acidity):
    """
    草食時の胃酸ペナルティ（胃酸が強いほど植物由来の栄養が破壊される）
    """
    return (1.0 - true_stomach_acidity) ** 3


@njit
def calc_bug_tooth_score(fangs):
    """
    虫の殻を砕く歯のスコア
    fangs=0.5（頑丈な円錐）が最強。0.0（平ら）や1.0（ナイフ）では効果半減。
    山なり曲線で表現。
    """
    return max(0.1, 1.0 - abs(fangs - 0.5) * 1.5)


# ------------------------------------------
# ❄️ 寒冷耐性系
# ------------------------------------------

@njit
def calc_insulation(keratin, keratin_type, keratin_complexity):
    """
    断熱性（寒冷耐性の素材部分）
    αケラチン × 単純構造 → 獣毛（高断熱）
    βケラチン × 複雑構造 → ダウン（高断熱）
    """
    alpha_fur_factor  = (1.0 - keratin_type) * (1.0 - keratin_complexity)
    beta_down_factor  = keratin_type * keratin_complexity
    return keratin * max(alpha_fur_factor, beta_down_factor)


@njit
def calc_cold_resistance(fat_ratio, keratin, keratin_type, keratin_complexity):
    """
    総合的な寒冷耐性（0.0〜1.0）
    脂肪による断熱 + ケラチン（毛・ダウン）による断熱
    """
    insulation = calc_insulation(keratin, keratin_type, keratin_complexity)
    return (fat_ratio * 0.5) + (insulation * 0.5)


# ------------------------------------------
# 🛡️ 戦闘・防御系
# ------------------------------------------

@njit
def calc_armor_value(keratin, keratin_type, keratin_complexity, size):
    """
    物理防御力（鱗の硬さ × 体サイズ補正）
    βケラチン × 単純構造（鱗）が最も防御力が高い
    """
    scale_factor = keratin_type * (1.0 - keratin_complexity)
    return (keratin * scale_factor) * (size / 3.0)


@njit
def calc_damage_multiplier(armor_value):
    """
    被ダメージ倍率（防御力から計算）
    armor=0で等倍ダメージ、armor高いほど軽減
    """
    return max(0.1, 1.0 - armor_value * 0.5)


# ------------------------------------------
# 🧬 遺伝的距離系
# ------------------------------------------

@njit
def calc_genetic_distance(
    fangs_i, fangs_j,
    sizes_i, sizes_j,
    speeds_i, speeds_j,
    aggros_i, aggros_j,
    intels_i, intels_j,
    acidities_i, acidities_j,
    forestomach_i, forestomach_j,
    intestine_i, intestine_j,
    cecum_i, cecum_j
):
    """
    全遺伝子距離（繁殖互換性の判定に使用）
    D < 0.4 で交配可能
    """
    D_sq = (
        (fangs_i       - fangs_j)                   ** 2 +
        ((sizes_i      - sizes_j)      / 3.0)        ** 2 +
        ((speeds_i     - speeds_j)     / 4.0)        ** 2 +
        (aggros_i      - aggros_j)                   ** 2 +
        (intels_i      - intels_j)                   ** 2 +
        (acidities_i   - acidities_j)                ** 2 +
        (forestomach_i - forestomach_j)              ** 2 +
        (intestine_i   - intestine_j)                ** 2 +
        (cecum_i       - cecum_j)                    ** 2
    )
    return D_sq ** 0.5


@njit
def calc_morpho_distance(
    fangs_i, fangs_j,
    sizes_i, sizes_j,
    intestine_i, intestine_j,
    acidities_i, acidities_j
):
    """
    形態的距離（同種判定に使用）
    行動形質（aggros/intels/fears）は無視し、体の構造で種を判定する。
    生物学的根拠：種の同一性は形態で決まる。
    M < 0.4 で同種
    """
    D_sq = (
        (fangs_i     - fangs_j)     ** 2 +
        (sizes_i     - sizes_j)     ** 2 +
        (intestine_i - intestine_j) ** 2 +
        (acidities_i - acidities_j) ** 2
    )
    return D_sq ** 0.5


# ------------------------------------------
# 🥩 肉の量
# ------------------------------------------

@njit
def calc_meat_yield(size, fat_ratio, keratin, keratin_type, keratin_complexity, intestine_len):
    """
    個体を倒したときに得られる肉の量
    質量に比例（大きく重い個体ほど肉が多い）
    """
    mass = calc_mass(size, fat_ratio, keratin, keratin_type, keratin_complexity, intestine_len)
    return mass * 15.0
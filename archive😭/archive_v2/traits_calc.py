def calc_bite_force(dna):
    """
    噛む力
    生物学的ロジック:テコの原理
    """
    muscle = dna.get('jaw_muscle_mass') # 噛む力
    snout = dna.get('skull_snout_length')#鼻の長さ
    scale = dna.get('head_scale')#頭のサイズ
    gape = dna.get('jaw_gape_angle')#口が開く角度

    #1.テコの原理
    leverge = 1.0 - (snout * 0.5)

    #2.絶対的スケール
    #scaleは0.0(ネズミ)~1.0(ティラノサウルス)のようなイメージ。指数関数的に増やすとリアル。
    absolute_mass = muscle * (scale ** 2) * 5000.0

    #大きく開きすぎるとペナルティ(カバや蛇の要素)
    #gapeが1.0(限界まで開く)だと筋肉が伸びきって力が20%落ちる
    gape_penalty = 1.0 - (gape * 0.2)

    #最終計算
    raw_farce = absolute_mass * leverge * gape_penalty

    return max(1.0, raw_farce)

def cale_base_metabolism(dna):
    """
    [基礎代謝（Base]
    生物学的ロジック:体重が重いほど燃費が悪い。
    肝臓や心臓は筋肉や脂肪より多くのカロリーを要求する。
    """
    #1.DNAから基礎データ取得
    head_scale = dna.get('head_scale', 0.4)
    jaw_muscle = dna.get('jaw_muscle_mass', 0.3)
    
    heart_muscle = dna.get('heart_muscle', 0.3)
    liver_size = dna.get('liver_size', 0.3)
    stomach_comp = dna.get('stomach_compartments', 0.0)
    intestine = dna.get('intestine_length', 0.3)
    fat = dna.get('fat_distribution', 0.5)

    #2.質量の計算
    head_weight = (head_scale ** 2) * (1.0 + jaw_muscle)
    organ_weight = head_scale + liver_size + stomach_comp + intestine

    #脂肪は維持コストはかからない。重い。
    total_mass = head_weight + organ_weight + (fat * 0.5)
    
    #3.臓器の維持コスト
    #肝臓は高性能だけどコストが2.5倍
    organ_cost_muitilier = 1.0 + (liver_size * 2.5) + (heart_muscle * 1.5)+(stomach_comp * 1.0)

    #4.最終計算
    raw_metabolism = total_mass * organ_cost_muitilier * 10.0

    return max(5.0, raw_metabolism)

def cale_vision_range(dna):
    """
    {状況把握}
    目の性能がいいほど遠くの餌をロックオンする
    """
    #太郎はまだ目が目が悪いので-.2
    eye_power = dna.get('eye_power',0.2)

    #索敵範囲。最低でも自分の周囲は見え、目がいいと広がる。
    vision = 10.0 + (eye_power * 100.0)

    return vision
def calc_vision_stats(dna):
    """
    視覚性能の計算
    目の位置と各器官の性能から視野角、立体視、燃費ペナルティを弾き出す。
    """
    placement = dna.get('eye_placement', 0.7)
    retina = dna.get('retina_density', 0.3)
    lens = dna.get('lens_focus', 0.3)
    nerve = dna.get('optic_nerve', 0.2)
    cortex = dna.get('visual_cortex', 0.2)

    #1.視野角
    #placementが0.0なら正面を向いているので120度、1.0なら340度
    fov_angle = 120 + (placement * 220)

    #2.立体視
    #正面を向いているほど視界が重なり立体視が高まる。さらに視覚野の処理が必要。
    #0.0(正確に距離がわかる) ~ 1.0(距離感がバグる。)
    depth_accuracy = (1.0 - placement) * cortex

    #3索敵距離
    #水晶体の性能が高いほど遠くまで見える。
    #水晶体の性能が高いほど遠くまで見える。
    max_distance = 10.0 + (lens * 50.0)

    #4.脳の消費ペナルティ
    brain_cost = (complex * 10.0) + (nerve * 5.0)
    return {
        'fov_angle':fov_angle,
        'depth_accuracy':depth_accuracy,
        'max_distance':max_distance,
        'brain_cost':brain_cost
    }


# ==========================================
# 🌏 terrain.py：Perlin Noise 地形生成エンジン
# ==========================================
#
# 【このファイルの役割】
# シミュレーション開始時に1回だけ呼ばれ、
# 自然な地形データ（高度・川・水分）を生成する。
#
# 【全体の流れ】
# perlin_noise_2d()  ← 基盤となるノイズ関数
#       ↓
# generate_altitude()  ← ノイズから高度マップを生成
#       ↓
# generate_river()     ← 高度が低い場所を川にする
#       ↓
# generate_moisture()  ← 高度＋川の位置から水分量を計算
#
# 【なぜ外部ライブラリを使わないのか？】
# `pip install noise` や `opensimplex` を使えば1行で済むが：
#   1. 学習目的: アルゴリズムの仕組みを理解する
#   2. 依存関係ゼロ: NumPyだけで完結（環境トラブルなし）
#   3. カスタマイズ性: パラメータを自由に変更できる
# ==========================================

import numpy as np
from config import *


# ------------------------------------------
# 🧮 1. Perlin Noiseの基本パーツ（補間関数）
# ------------------------------------------

def _fade(t):
    """パーリンの改良スムーズステップ関数
    
    【なぜこの関数が必要？】
    
    Perlin Noiseでは、格子点（整数座標）の間を「補間（ブレンド）」して
    なめらかなノイズを作る。最も素朴な方法は「線形補間」（直線で結ぶ）だが、
    これだと格子点の境界で「折れ線」のようにカクカクしてしまう。
    
    この関数は Ken Perlin が考案した5次多項式で、以下の特性を持つ：
    - f(0) = 0, f(1) = 1         → 端点で正しい値
    - f'(0) = 0, f'(1) = 0       → 端点で傾きがゼロ（なめらか）
    - f''(0) = 0, f''(1) = 0     → 端点で曲率もゼロ（超なめらか）
    
    数式: f(t) = 6t⁵ - 15t⁴ + 10t³
    
    【具体例】
    t=0.0 → 0.0（完全にA寄り）
    t=0.5 → 0.5（AとBの中間、ちょうど半分）
    t=1.0 → 1.0（完全にB寄り）
    t=0.1 → 0.028（Aにかなり近い、でもゼロじゃない → なめらかに離れる）
    """
    return t * t * t * (t * (t * 6 - 15) + 10)


def _lerp(a, b, t):
    """線形補間 (Linear Interpolation = lerp)
    
    【なぜこの関数が必要？】
    2つの値 a と b の「間」を取る、プログラミングで最も基本的な関数。
    ゲーム開発・CG・科学計算のあらゆる場面で登場する。
    
    t = 0.0 → a を返す（完全にaの影響）
    t = 0.5 → (a+b)/2 を返す（半々のブレンド）
    t = 1.0 → b を返す（完全にbの影響）
    
    Perlin Noiseでは、4つの格子点の値をブレンドするために
    この関数を2回（X方向→Y方向）使う。これを「双線形補間」と呼ぶ。
    """
    return a + t * (b - a)


# ------------------------------------------
# 🗻 2. Perlin Noise 生成器（このファイルの心臓部）
# ------------------------------------------

def perlin_noise_2d(shape, scale=10.0, octaves=4, persistence=0.5, seed=42):
    """2D Perlin Noiseマップを生成する
    
    ============================================
    【アルゴリズムの全体像（3ステップ）】
    ============================================
    
    STEP 1: 格子点にランダムな「勾配ベクトル」を配置
    ─────────────────────────────────────────
    - 格子点 = 整数座標 (0,0), (0,1), (1,0), (1,1), ... の交差点
    - 各格子点にランダムな方向の「矢印（ベクトル）」を置く
    - この矢印が「この付近の地形はどの方向に傾いているか」を決める
    
    例: 格子点(0,0)に→（右向き）の矢印があると、
        (0,0)の右側は高く、左側は低い地形になる
    
    STEP 2: 各ピクセルについて4つの格子点との関係を計算
    ─────────────────────────────────────────
    - 各ピクセルは、周囲4つの格子点に囲まれている
    - 4つの格子点それぞれについて：
      「格子点の勾配ベクトル」と「格子点→ピクセルの距離ベクトル」
      の内積（ドット積）を計算
    - 内積 = 2つのベクトルの方向が揃っているほど大きい値
    
    STEP 3: 4つの内積値をスムーズ補間でブレンド
    ─────────────────────────────────────────
    - _fade() で滑らかにした補間係数を使い
    - _lerp() でX方向→Y方向の順にブレンド
    - → そのピクセルの最終ノイズ値が決まる
    
    ============================================
    【フラクタルノイズ（オクターブの重ね合わせ）】
    ============================================
    
    上の3ステップで1枚のノイズが作れるが、それだけだと
    「なだらかすぎる」地形になる。現実の地形は：
    
    大きな山脈 + 中くらいの丘 + 小さな起伏 + 微細な凸凹
    
    が重なっている。これを再現するために、異なる「周波数」の
    ノイズを重ね合わせる。これを「フラクタルノイズ」と呼ぶ。
    
    1回目（octave=0）: 大きな山脈  振幅=1.0  周波数=1
    2回目（octave=1）: 中くらいの丘 振幅=0.5  周波数=2
    3回目（octave=2）: 小さな起伏  振幅=0.25 周波数=4
    4回目（octave=3）: 微細な凸凹  振幅=0.125 周波数=8
    
    Parameters:
        shape: (rows, cols) 出力配列のサイズ
        scale: 空間スケール（大きいほど地形特徴が大きい）
        octaves: 重ね合わせの回数（多いほど細かいディテールが増える）
        persistence: 各オクターブでの振幅減衰率（0.5 = 半分ずつ小さくなる）
        seed: 乱数シード（同じ値なら同じ地形が再現される）
    
    Returns:
        0.0〜1.0 に正規化された2D NumPy配列
    """
    # ━━━ 乱数生成器の初期化 ━━━
    # np.random.RandomState: seedを固定した独立した乱数生成器
    # グローバルなnp.randomに影響を与えないため、再現性が高い
    rng = np.random.RandomState(seed)
    rows, cols = shape
    
    # 全オクターブの結果を蓄積する配列
    noise = np.zeros((rows, cols))
    
    # 振幅の管理変数
    amplitude = 1.0       # 現在のオクターブの振幅（重み）
    max_amplitude = 0.0   # 正規化用の振幅合計
    
    for octave in range(octaves):
        # ━━━ このオクターブの周波数とスケールを計算 ━━━
        # octave=0 → freq=1（大きな山）  scale=8.0
        # octave=1 → freq=2（中くらい）  scale=4.0
        # octave=2 → freq=4（小さい）    scale=2.0
        # octave=3 → freq=8（微細）      scale=1.0
        freq = 2 ** octave
        current_scale = scale / freq
        
        # ━━━ STEP 1: 格子点に勾配ベクトルを配置 ━━━
        # 格子のサイズ = ピクセル数 / スケール（+2は配列の境界対策）
        grid_h = int(np.ceil(rows / current_scale)) + 2
        grid_w = int(np.ceil(cols / current_scale)) + 2
        
        # 各格子点にランダムな角度（0〜2π）を割り当て
        # → cos/sin で2Dの勾配ベクトル（単位ベクトル）に変換
        #
        # なぜ角度→cos/sinなのか？
        # 単位円上の点 (cos θ, sin θ) は長さ1のベクトルを表す。
        # 角度をランダムにすれば、全方向に均等な勾配が作れる。
        angles = rng.uniform(0, 2 * np.pi, (grid_h, grid_w))
        grad_x = np.cos(angles)  # 勾配ベクトルのX成分
        grad_y = np.sin(angles)  # 勾配ベクトルのY成分
        
        # ━━━ STEP 2: 全ピクセルの座標をノイズ空間に変換 ━━━
        # np.meshgrid: 1次元配列から2次元の座標グリッドを一括生成
        # これにより forループなしで全ピクセルを同時に処理できる（ベクトル化）
        #
        # indexing='ij' は「行列形式」(row, col) の順序で出力する指定。
        # デフォルトの 'xy' だと (col, row) 順になり混乱するため、
        # 配列の添字と一致する 'ij' を使う。
        y_coords = np.arange(rows) / current_scale
        x_coords = np.arange(cols) / current_scale
        yy, xx = np.meshgrid(y_coords, x_coords, indexing='ij')
        
        # 各ピクセルが属する格子セルの左上の整数座標
        x0 = np.floor(xx).astype(int)
        y0 = np.floor(yy).astype(int)
        
        # セル内での小数部分（0.0〜1.0）
        # 例: x=3.7 のとき、x0=3, fx=0.7（セルの右寄り）
        fx = xx - x0
        fy = yy - y0
        
        # ━━━ STEP 3: 4つの格子点との内積を計算 ━━━
        #
        # 【図解】1つの格子セルとピクセルPの位置関係
        #
        #  (y0,x0)─────────(y0,x0+1)
        #     │               │
        #     │     ・P        │    P = 現在のピクセル
        #     │   (fx, fy)     │    矢印 = 各格子点の勾配ベクトル
        #     │               │
        #  (y0+1,x0)────(y0+1,x0+1)
        #
        # 各格子点について：
        #   内積 = 勾配ベクトル ・ (格子点→Pのベクトル)
        #
        # 左上(y0,x0)からPへ: ベクトル = (fx, fy)
        n00 = grad_x[y0, x0] * fx       + grad_y[y0, x0] * fy
        # 右上(y0,x0+1)からPへ: ベクトル = (fx-1, fy)  ← x方向は逆
        n10 = grad_x[y0, x0+1] * (fx-1) + grad_y[y0, x0+1] * fy
        # 左下(y0+1,x0)からPへ: ベクトル = (fx, fy-1)  ← y方向は逆
        n01 = grad_x[y0+1, x0] * fx     + grad_y[y0+1, x0] * (fy-1)
        # 右下(y0+1,x0+1)からPへ: ベクトル = (fx-1, fy-1)
        n11 = grad_x[y0+1, x0+1]*(fx-1) + grad_y[y0+1, x0+1]*(fy-1)
        
        # ━━━ STEP 4: スムーズ補間で4つの値をブレンド ━━━
        u = _fade(fx)  # X方向の補間係数（_fadeで滑らかにする）
        v = _fade(fy)  # Y方向の補間係数
        
        # 双線形補間（Bilinear Interpolation）
        # まずX方向に補間（上辺と下辺で別々に）
        nx0 = _lerp(n00, n10, u)  # 上辺: 左上と右上をブレンド
        nx1 = _lerp(n01, n11, u)  # 下辺: 左下と右下をブレンド
        
        # 次にY方向に補間（上辺結果と下辺結果をブレンド）
        value = _lerp(nx0, nx1, v)
        
        # ━━━ このオクターブの結果を加算 ━━━
        noise += value * amplitude
        max_amplitude += amplitude
        amplitude *= persistence  # 次のオクターブでは振幅を小さくする
    
    # ━━━ 0.0〜1.0 に正規化 ━━━
    # Perlin Noiseの生値は負の値も取りうるため、
    # 全体を[0, 1]の範囲に収める
    noise = (noise - noise.min()) / (noise.max() - noise.min() + 1e-10)
    return noise


# ------------------------------------------
# 🏔️ 3. 地形グリッド生成（ゲームワールドの基盤）
# ------------------------------------------

def generate_altitude(shape, seed=TERRAIN_SEED):
    """高度マップを生成する
    
    【なぜ高度が「最初」に生成されるのか？】
    
    現実世界でも、このシミュレーションでも、地形の高度が
    他のすべての環境要因を決定する「親」にあたる：
    
    高度（ここで生成）
      └→ 川の位置（水は高い→低いに流れる）
           └→ 水分量（川の近くは湿潤、高地は乾燥）
                └→ 植物の成長量（process_plants が参照）
                     └→ 動物の生存（食料供給の分布）
    
    この「因果の連鎖」を正しく設計することで、
    仕様書の「環境圧から進化を創発させる」が実現する。
    
    Returns:
        (GRID_SIZE, GRID_SIZE) の float32 配列（0.0〜1.0）
        0.0 = 海面/最低地、1.0 = 山頂
    """
    print("🏔️ 高度マップを生成中...")
    altitude = perlin_noise_2d(
        shape, 
        scale=TERRAIN_SCALE,     # 地形の大きさ（config.pyで定義）
        octaves=TERRAIN_OCTAVES, # ディテールの細かさ
        persistence=0.5,         # 標準的な減衰率
        seed=seed
    )
    return altitude.astype(np.float32)


def generate_river(altitude_grids, threshold=RIVER_THRESHOLD):
    """高度マップから川の位置を決定する
    
    【なぜ高度から川を決めるのか？】
    
    現実の川は「水が高いところから低いところに流れる」ことで形成される。
    完全な流体シミュレーションは計算が重すぎるので、ここでは簡易的に：
    
    「高度が閾値（threshold）以下の谷を川とする」
    
    というアプローチを取る。Perlin Noiseの高度マップは自然な山谷を持つため、
    この単純なルールだけで、蛇行する川のような地形が自然に生まれる。
    
    【river_depth（川の深さ）の設計】
    
    Step 1で実装した engine.py の「深さに比例するスタミナ消費」が
    ここで活きてくる。river_depth の値が大きいほど：
    - スタミナ消費が激しい（溺れやすい）
    - エネルギーダメージも増加
    
    高度0.0（最低地点）→ river_depth=1.0（最も深い川）
    高度=threshold     → river_depth=0.0（川の端、浅い）
    
    Returns:
        (rows, cols) の float32 配列
        0.0 = 陸地、0.0〜1.0 = 川の深さ
    """
    print("🌊 川を配置中...")
    rows, cols = altitude_grids.shape
    river = np.zeros((rows, cols), dtype=np.float32)
    
    for r in range(rows):
        for c in range(cols):
            alt = altitude_grids[r, c]
            if alt < threshold:
                # 高度が低いほど川が深い
                # 例: threshold=0.25 のとき
                #   alt=0.00 → depth=1.0（最深部）
                #   alt=0.10 → depth=0.6
                #   alt=0.20 → depth=0.2（浅い岸辺）
                #   alt=0.25 → depth=0.0（ちょうど境界）
                river[r, c] = 1.0 - (alt / threshold)
    
    river_cells = np.sum(river > 0)
    print(f"   → 川セル数: {river_cells} / {rows * cols} "
          f"({river_cells * 100 / (rows * cols):.1f}%)")
    return river


def generate_moisture(altitude_grids, river_grids):
    """高度と川の位置から水分量を計算する
    
    【水分量を決める3つの要因】
    
    1. 川からの水分拡散（最も重要）
       現実: 河川の周囲は「氾濫原」と呼ばれ、肥沃で水分豊富
       実装: 川のセルを中心に、周囲に水分が「にじみ出す」
             距離が遠いほど水分は弱くなる（逆二乗の法則で減衰）
    
    2. 高度による補正
       現実: 山頂は風が強く乾燥、谷底は水が溜まる
       実装: altitude が低いほど moisture にボーナス
    
    3. 最終クランプ: 0.0〜1.0 の範囲に制限
    
    【なぜ3つの要因を組み合わせるのか？】
    
    1つだけだと不自然になる：
    - 川だけ → 川から離れると突然砂漠（不自然な断崖）
    - 高度だけ → 低地が全部湿地帯になる（川の恩恵がない）
    - 両方 → 「川沿いの低地=ジャングル、高山=草原、乾いた台地=砂漠」
              自然な環境グラデーションが生まれる
    
    Returns:
        (rows, cols) の float32 配列（0.0=砂漠 〜 1.0=オアシス）
    """
    print("💧 水分量を計算中...")
    rows, cols = altitude_grids.shape
    moisture = np.zeros((rows, cols), dtype=np.float32)
    
    # ━━━ 要因1: 川からの水分拡散 ━━━
    # 川のセルを中心に、半径SPREAD_RANGEの範囲に水分が広がる
    # 距離が遠いほど水分は弱くなる（逆二乗の法則）
    #
    # 【なぜ逆二乗の法則？】
    # 水分の拡散は物理的には距離に応じて減衰する。
    # 正確には指数減衰 e^(-d) が近いが、計算が簡単で
    # 見た目も自然な 1/(1+d²) を採用している。
    SPREAD_RANGE = 5  # 川の影響範囲（5セル ≈ ワールド座標で10単位）
    
    for r in range(rows):
        for c in range(cols):
            if river_grids[r, c] > 0.0:
                # 川のセル自体は水分MAX
                moisture[r, c] = max(moisture[r, c], 1.0)
                
                # 周囲のセルに水分を拡散
                for dr in range(-SPREAD_RANGE, SPREAD_RANGE + 1):
                    for dc in range(-SPREAD_RANGE, SPREAD_RANGE + 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            dist = np.sqrt(dr * dr + dc * dc)
                            if dist > 0:
                                # 逆二乗法則: 近い→強い、遠い→弱い
                                spread = river_grids[r, c] / (1.0 + dist * dist * 0.5)
                                # max: 既に高い水分は上書きしない
                                moisture[nr, nc] = max(moisture[nr, nc], spread)
    
    # ━━━ 要因2: 高度による補正 ━━━
    # 低地（altitude≈0）ほど水分にボーナス、高地ほど乾燥
    # (1.0 - altitude) * 0.3 → 最大0.3のボーナス
    altitude_bonus = (1.0 - altitude_grids) * 0.3
    moisture += altitude_bonus
    
    # ━━━ 0.0〜1.0 にクランプ ━━━
    # np.clip: 値の範囲を制限する関数
    # 水分量が1.0を超えることは物理的に意味がないため
    moisture = np.clip(moisture, 0.0, 1.0)
    
    print(f"   → 水分: min={moisture.min():.2f}, max={moisture.max():.2f}, "
          f"mean={moisture.mean():.2f}")
    return moisture

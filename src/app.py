# ==========================================
# 🌐 app.py：Flaskサーバー＆メインループ (植物グリッド対応版)
# ==========================================
from flask import Flask, render_template
from flask_socketio import SocketIO
import numpy as np
import time
from config import *
import engine
import terrain  # 🌏 NEW: Perlin Noise地形生成
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') 
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 🧬 【太郎系データ】
taro_x = np.zeros(MAX_TARO, dtype=np.float32)
taro_y = np.zeros(MAX_TARO, dtype=np.float32)
taro_alive = np.zeros(MAX_TARO, dtype=np.bool_)
t_energies = np.zeros(MAX_TARO, dtype=np.float32)
t_speeds = np.zeros(MAX_TARO, dtype=np.float32)
t_visions = np.zeros(MAX_TARO, dtype=np.float32)
t_fangs = np.zeros(MAX_TARO, dtype=np.float32)
t_sizes = np.zeros(MAX_TARO, dtype=np.float32)
t_angles = np.zeros(MAX_TARO, dtype=np.float32)
t_ages = np.zeros(MAX_TARO, dtype=np.int32)


# 🧠 【性格・AI系データ】
t_aggros = np.zeros(MAX_TARO, dtype=np.float32)
t_intels = np.zeros(MAX_TARO, dtype=np.float32)
t_fears = np.zeros(MAX_TARO, dtype=np.float32)

# 🫀 【内臓系データ】
t_true_stomach_acidities = np.zeros(MAX_TARO, dtype=np.float32)
t_forestomach_capas = np.zeros(MAX_TARO, dtype=np.float32)
t_cecum_sizes = np.zeros(MAX_TARO, dtype=np.float32)
t_intestine_lens = np.zeros(MAX_TARO, dtype=np.float32)

# 🏃‍♂️ NEW: 【運動・スタミナ系データ】
t_current_speeds = np.zeros(MAX_TARO, dtype=np.float32) # 現在出そうとしている速度
t_staminas = np.zeros(MAX_TARO, dtype=np.float32)       # 現在のスタミナ残量
t_max_staminas = np.zeros(MAX_TARO, dtype=np.float32)   # スタミナ最大値 (タンク容量)
t_lung_capas = np.zeros(MAX_TARO, dtype=np.float32)     # 肺活量 (回復力)
t_muscle_ratio = np.zeros(MAX_TARO, dtype=np.float32)   # 筋肉タイプ (0.0:赤筋 〜 1.0:白筋)

# 🧬 NEW: 【環境適応・体表系データ（Step 3）】
t_metabolisms = np.zeros(MAX_TARO, dtype=np.float32)           # 基礎代謝
t_fat_ratios = np.zeros(MAX_TARO, dtype=np.float32)            # 脂肪蓄積率
t_keratins = np.zeros(MAX_TARO, dtype=np.float32)              # ケラチン量（体表の厚さ）
t_keratin_types = np.zeros(MAX_TARO, dtype=np.float32)         # ケラチン基底タイプ (0.0:α哺乳類 〜 1.0:β爬虫鳥類)
t_keratin_complexities = np.zeros(MAX_TARO, dtype=np.float32)  # ケラチン構造の複雑さ (0.0:管/板 〜 1.0:枝分かれ)
t_nerve_densities = np.zeros(MAX_TARO, dtype=np.float32)       # 神経密集度（感覚毛）

# 🧬 【太郎系データ】の下あたりに追加！
t_microbiome = np.zeros(MAX_TARO, dtype=np.float32)
t_cooldowns = np.zeros(MAX_TARO, dtype=np.int32) # 🌟 NEW: 妊娠・交尾のクールダウン


# 🌱 【環境系データ（肉・そして「植物グリッド」）】
meat_x = np.zeros(MAX_MEAT, dtype=np.float32)
meat_y = np.zeros(MAX_MEAT, dtype=np.float32)
meat_amount = np.zeros(MAX_MEAT, dtype=np.float32)
meat_active = np.zeros(MAX_MEAT, dtype=np.bool_)
meat_age = np.zeros(MAX_MEAT, dtype=np.int32)
# 🌟 NEW: 植物と虫は「10x10の面（グリッド）」で管理する！

tree_grids = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)  # 🌟 NEW
grass_grids = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32) # 🌟 NEW
bug_grids = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
temperature_grids = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)

# 🌏 【地形系データ】
altitude_grids = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)  # 🏔️ 高度
moisture_grids = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)  # 💧 水分量
river_grids = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)     # 🌊 川の深さ

# 🗺️ 【空間グリッド＆通信バッファ】
# 🌟 FIX: 点の植物（f_counts等）を全削除！
m_counts = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int32)
m_idx = np.full((GRID_SIZE, GRID_SIZE, 500), -1, dtype=np.int32)
t_counts = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int32)
t_idx = np.full((GRID_SIZE, GRID_SIZE, 50), -1, dtype=np.int32)

buffer_taro = np.zeros(MAX_TARO * 8, dtype=np.float32)
buffer_plants = np.zeros(GRID_SIZE * GRID_SIZE * 2, dtype=np.float32) # 🌟 NEW: 植物の濃淡を送るバッファ
buffer_meat = np.zeros(MAX_MEAT * 2, dtype=np.float32)
death_stats = np.zeros(4, dtype=np.int64)


def save_evolution_graph(taro_alive, t_fangs, t_intestine_lens, frame_count):
    alive_idx = np.where(taro_alive)[0]
    if len(alive_idx) == 0: return
    
    plt.figure(figsize=(8, 6))
    plt.scatter(t_fangs[alive_idx], t_intestine_lens[alive_idx], alpha=0.3, c='blue', s=10)
    plt.title(f"Evolution: Fangs vs Intestine (Frame: {frame_count})")
    plt.xlabel("Fangs (0.0: Herbivore <---> 1.0: Carnivore)")
    plt.ylabel("Intestine Length")
    plt.xlim(-0.1, 1.1)
    plt.ylim(-0.1, 1.1)
    plt.grid(True, linestyle='--', alpha=0.6)

    # 🌟 固定ファイル名で上書き保存
    os.makedirs("graphs", exist_ok=True)
    plt.savefig("graphs/evolution_latest.png")
    plt.close()

def save_stamina_graph(taro_alive, t_muscle_ratio, t_lung_capas, t_fangs, frame_count):
    alive_idx = np.where(taro_alive)[0]
    if len(alive_idx) == 0: return

    # 食性による色分けロジック
    colors = np.zeros((len(alive_idx), 4))
    fangs = t_fangs[alive_idx]
    for i, f in enumerate(fangs):
        if f <= 0.2: colors[i] = [0.2, 0.8, 0.2, 0.5] # 緑
        elif f >= 0.8: colors[i] = [0.8, 0.2, 0.2, 0.5] # 赤
        else: colors[i] = [0.8, 0.8, 0.2, 0.5] # 黄

    plt.figure(figsize=(8, 6))
    plt.scatter(t_muscle_ratio[alive_idx], t_lung_capas[alive_idx], c=colors, s=15)
    plt.title(f"Stamina & Muscle: Recovery vs Speed (Frame: {frame_count})")
    plt.xlabel("Muscle Ratio (0:Red/Slow <---> 1:White/Fast)")
    plt.ylabel("Lung Capacity (Recovery)")
    plt.xlim(-0.1, 1.1)
    plt.ylim(-0.1, 1.1)
    plt.grid(True, linestyle='--', alpha=0.6)

    # 🌟 固定ファイル名で上書き保存
    os.makedirs("graphs", exist_ok=True)
    plt.savefig("graphs/stamina_latest.png")
    plt.close()

def save_digestion_graph(taro_alive, t_forestomach_capas, t_cecum_sizes, t_fangs, frame_count):
    alive_idx = np.where(taro_alive)[0]
    if len(alive_idx) == 0: return

    # 食性による色分けロジック（緑:草食, 赤:肉食, 黄:雑食）
    colors = np.zeros((len(alive_idx), 4))
    fangs = t_fangs[alive_idx]
    for i, f in enumerate(fangs):
        if f <= 0.2: colors[i] = [0.2, 0.8, 0.2, 0.5] 
        elif f >= 0.8: colors[i] = [0.8, 0.2, 0.2, 0.5] 
        else: colors[i] = [0.8, 0.8, 0.2, 0.5] 

    plt.figure(figsize=(8, 6))
    plt.scatter(t_forestomach_capas[alive_idx], t_cecum_sizes[alive_idx], c=colors, s=15)
    plt.title(f"Digestion Evolution: Forestomach vs Cecum (Frame: {frame_count})")
    plt.xlabel("Forestomach Capacity (Cow-like / Foregut Fermenter)")
    plt.ylabel("Cecum Size (Horse-like / Hindgut Fermenter)")
    plt.xlim(-0.1, 1.1)
    plt.ylim(-0.1, 1.1)
    plt.grid(True, linestyle='--', alpha=0.6)

    os.makedirs("graphs", exist_ok=True)
    plt.savefig("graphs/digestion_latest.png")
    plt.close()

def save_size_graph(taro_alive, t_sizes, t_speeds, t_fangs, frame_count):
    alive_idx = np.where(taro_alive)[0]
    if len(alive_idx) == 0: return

    # 食性による色分けロジック（緑:草食, 赤:肉食, 黄:雑食）
    colors = np.zeros((len(alive_idx), 4))
    fangs = t_fangs[alive_idx]
    for i, f in enumerate(fangs):
        if f <= 0.2: colors[i] = [0.2, 0.8, 0.2, 0.5] 
        elif f >= 0.8: colors[i] = [0.8, 0.2, 0.2, 0.5] 
        else: colors[i] = [0.8, 0.8, 0.2, 0.5] 

    plt.figure(figsize=(8, 6))
    plt.scatter(t_sizes[alive_idx], t_speeds[alive_idx], c=colors, s=15)
    plt.title(f"Size vs Speed (Frame: {frame_count})")
    plt.xlabel("Body Size (0.5: Small <---> 3.0: Large)")
    plt.ylabel("Base Speed")
    plt.xlim(0.0, 3.5)
    plt.ylim(0.0, 4.5)
    plt.grid(True, linestyle='--', alpha=0.6)

    # 🌟 サイズとスピードのグラフとして保存
    os.makedirs("graphs", exist_ok=True)
    plt.savefig("graphs/size_latest.png")
    plt.close()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """クライアント接続時に地形データを送信（1回だけ）
    
    【なぜ接続時に送るのか？】
    地形はシミュレーション中に変化しないから、
    毎フレーム送る必要はない。クライアントが接続した
    瞄間に1回だけ送ることで帯域を節約する。
    """
    if np.any(altitude_grids > 0):
        terrain_buf = np.zeros(GRID_SIZE * GRID_SIZE * 3, dtype=np.float32)
        terrain_buf[0::3] = altitude_grids.ravel()
        terrain_buf[1::3] = river_grids.ravel()
        terrain_buf[2::3] = moisture_grids.ravel()
        socketio.emit('terrain_data', terrain_buf.tobytes())

def run_simulation():
    print("🌍 宇宙を初期化中...")
    
    # 🏔️ Perlin Noiseによる地形生成
    altitude_grids[:] = terrain.generate_altitude((GRID_SIZE, GRID_SIZE))
    river_grids[:] = terrain.generate_river(altitude_grids)
    moisture_grids[:] = terrain.generate_moisture(altitude_grids, river_grids)
    
    # 🌿 NEW: 植物の初期化（虫が発生するために必須）
    # 木の初期分布：水分に比例＋ランダム
    tree_grids[:] = np.random.uniform(80.0, 300.0, (GRID_SIZE, GRID_SIZE)) * moisture_grids
    tree_grids[:] = np.maximum(0.0, np.minimum(tree_grids, 600.0))
    
    # 草の初期分布：水分に比例＋樹冠ペナルティを考慮
    initial_shade = np.maximum(0.0, np.minimum(1.0, (tree_grids - 300.0) / 300.0))
    grass_grids[:] = np.random.uniform(200.0, 500.0, (GRID_SIZE, GRID_SIZE)) * moisture_grids * (1.0 - initial_shade)
    grass_grids[:] = np.maximum(0.0, grass_grids)
    
    # 虫の初期分布：草に依存して自動計算
    bug_grids[:] = (grass_grids * 1.5) - (tree_grids * 0.8)
    bug_grids[:] = np.maximum(0.0, bug_grids)
    
    print(f"🌳 初期木密度: min={tree_grids.min():.1f}, max={tree_grids.max():.1f}, mean={tree_grids.mean():.1f}")
    print(f"🌿 初期草密度: min={grass_grids.min():.1f}, max={grass_grids.max():.1f}, mean={grass_grids.mean():.1f}")
    print(f"🦗 初期虫密度: min={bug_grids.min():.1f}, max={bug_grids.max():.1f}, mean={bug_grids.mean():.1f}")
    
    for i in range(1000):
        # 🌊 川の上に生まれないようにする（陸地を探す）
        for _attempt in range(100):
            x = np.random.uniform(0, WORLD_SIZE)
            y = np.random.uniform(0, WORLD_SIZE)
            gx = max(0, min(int(x / GRID_SCALE), GRID_SIZE - 1))
            gy = max(0, min(int(y / GRID_SCALE), GRID_SIZE - 1))
            if river_grids[gy, gx] < 0.5:  # 川でない場所にスポーン
                break
        taro_x[i], taro_y[i] = x, y
        t_speeds[i] = np.random.uniform(1.0, 3.0)
        t_visions[i] = 10.0
        
        # 🌟 イクチオステガ仕様（肉食）！
       # 🌟 虫食最適値（0.5）を中心としたガウス分布
        # 多様性を保ちつつ、虫食効率が高い個体を優遇する
        t_fangs[i] = np.random.normal(0.5, 0.10)  # 平均 0.5, 標準偏差 0.10
        t_fangs[i] = np.clip(t_fangs[i], 0.0, 1.0)  # 0.0～1.0 の範囲に制限
        # 単位をmと定義
        # 初期値：イクチオステガ ≈ 1.0m
        t_sizes[i] = np.random.uniform(0.8, 1.2)
        
        # 闘争本能は普通（虫メインだけど、たまに共食いする）
        t_aggros[i] = np.random.uniform(0.3, 0.7) 
        t_intels[i] = np.random.uniform(0.0, 1.0)
        t_fears[i] = np.random.uniform(0.0, 1.0) 
        
        # 🌟 胃酸強め（虫の殻を溶かす）、腸は短い
        t_true_stomach_acidities[i] = 0.77 
        t_forestomach_capas[i] = 0.0
        t_cecum_sizes[i] = 0.0
        t_intestine_lens[i] = 0.3

        # 🏃‍♂️ NEW: スタミナ・運動器官の初期化（インデックス[i]で個別に代入！）
        t_max_staminas[i] = np.random.uniform(50.0, 200.0)
        t_staminas[i] = t_max_staminas[i]
        t_lung_capas[i] = np.random.uniform(0.1, 1.0)
        t_muscle_ratio[i] = np.random.uniform(0.0, 1.0)

        # 🧬 NEW: 環境適応系の初期化
        t_metabolisms[i] = np.random.uniform(0.2, 0.8)
        t_fat_ratios[i] = np.random.uniform(0.1, 0.5)
        t_keratins[i] = np.random.uniform(0.0, 0.3)             # 最初は少しだけ
        t_keratin_types[i] = np.random.choice([0.0, 1.0])       # αかβのどちらかに極端に振る（系統の決定）
        t_keratin_complexities[i] = np.random.uniform(0.0, 0.2) # 最初は単純な構造
        t_nerve_densities[i] = np.random.uniform(0.0, 0.3)

        # 初期エネルギー（虫を主食にして生き延びる）
        # 🌟 NEW: 初期エネルギーを動的に計算
        # 最初の 1000フレーム（植物成長期）を生き延びるために必要なエネルギーを計算
        size = t_sizes[i]  # 0.8 ~ 1.2
        speed = t_speeds[i]  # 1.0 ~ 3.0
        
        # 基本維持コスト（初期化で使用される値）
        organ_cost = 0.0  # 初期状態では内臓は未発達
        base_cost = 0.1 + ((size ** 2) * 0.15) + (speed * 0.05)
        metabolism_multiplier = 0.5 + t_metabolisms[i]
        
        daily_cost = base_cost * metabolism_multiplier
        survival_frames = 1000  # 虫が発生するまでの時間
        min_energy = daily_cost * survival_frames * 1.5  # 安全係数 1.5
        
        # 初期エネルギーを設定（最小 1000, 最大 3000）
        t_energies[i] = max(1000.0, min(3000.0, min_energy))
        
        print(f"  個体 {i}: 体サイズ {size:.2f}, 必要エネルギー {min_energy:.1f} → 割当 {t_energies[i]:.1f}") 
        taro_alive[i] = True

    print("✨ シミュレーション開始！")
    frame_count = 0
    while True:
        start_time = time.time()
        frame_count += 1

        # ====================================================
        # 🌍 Layer 0: Planetary Update (気候と季節)
        # ====================================================
        # climate_phase: 0.0 (春) -> 0.25 (夏) -> 0.5 (秋) -> 0.75 (冬) -> 1.0 (春)
        climate_phase = (frame_count % YEAR_LENGTH) / float(YEAR_LENGTH)
        
        # 太陽の高さ（夏至で最高、冬至で最低）: -1.0 〜 1.0
        sun_angle = np.sin(climate_phase * 2.0 * np.pi - np.pi/2.0)
        
        # 🌡️ グローバル気温: 夏は25度、冬は-5度前後
        global_temperature = 10.0 + sun_angle * 15.0
        
        # ☀️ 日照量: 冬は減る (0.2 〜 1.0)
        global_sunlight = 0.6 + sun_angle * 0.4
        global_sunlight = max(0.0, min(1.0, global_sunlight))

        # ====================================================
        # エンジン処理
        # ====================================================
        # 🌟 NEW: 植物の成長処理（気温と日照に依存）
        engine.update_temperature_grids(temperature_grids, altitude_grids, sun_angle)

        engine.process_plants(tree_grids, grass_grids, moisture_grids, temperature_grids, global_sunlight)

        engine.build_grids(meat_x, meat_y, meat_active, taro_x, taro_y, taro_alive, m_counts, m_idx, t_counts, t_idx)
        
        # 各関数に必要なグリッドデータを渡す
        engine.update_ai_integrated(taro_x, taro_y, taro_alive, t_energies, t_visions, t_fangs, t_sizes, t_aggros, t_intels, t_fears, t_angles, meat_x, meat_y, meat_active, m_counts, m_idx, t_counts, t_idx, t_true_stomach_acidities, t_forestomach_capas, t_intestine_lens, t_microbiome, grass_grids, t_speeds, t_current_speeds, river_grids, t_keratins, t_nerve_densities)
        
        engine.update_movement_and_stamina(taro_x, taro_y, taro_alive, t_angles, t_speeds, t_current_speeds, t_sizes, t_staminas, t_max_staminas, t_lung_capas, t_muscle_ratio, t_energies, river_grids, t_fat_ratios, t_keratins, t_keratin_types, t_keratin_complexities, temperature_grids,t_intestine_lens)
        
        engine.process_interactions(taro_x, taro_y, taro_alive, t_energies, t_fangs, t_sizes, t_true_stomach_acidities, t_forestomach_capas, t_intestine_lens, t_cecum_sizes, t_speeds, t_visions, t_aggros, t_intels, t_fears, meat_x, meat_y, meat_amount, meat_active, m_counts, m_idx, t_counts, t_idx, t_ages, t_microbiome, grass_grids, death_stats, t_max_staminas, t_lung_capas, t_muscle_ratio, t_staminas, meat_age, t_cooldowns, t_metabolisms, t_fat_ratios, t_keratins, t_keratin_types, t_keratin_complexities, t_nerve_densities)

        engine.process_life_cycle(taro_x, taro_y, taro_alive, t_energies, t_speeds, t_visions, t_fangs, t_sizes, t_aggros, t_intels, t_true_stomach_acidities, t_forestomach_capas, t_intestine_lens, t_cecum_sizes, meat_x, meat_y, meat_amount, meat_active, t_ages, death_stats, meat_age, t_cooldowns, t_metabolisms, t_keratins, t_nerve_densities)        

        engine.process_meat_decay(meat_amount, meat_active, meat_age)
        
        engine.update_microbiome_survival(taro_alive, t_microbiome, t_sizes, t_true_stomach_acidities, t_forestomach_capas, t_cecum_sizes)
        
        engine.process_bugs(taro_x, taro_y, taro_alive, t_energies, t_true_stomach_acidities, t_microbiome, bug_grids, tree_grids, grass_grids, t_fangs)
        
        engine.debug_energy_trace(taro_alive, t_energies, t_sizes, t_speeds, t_ages, frame_count, interval=100)

        # ====================================================
        # 荷造りと送信
        # ====================================================
        t_len = engine.extract_taro_render_data(taro_x, taro_y, taro_alive, t_speeds, t_visions, t_fangs, t_sizes, t_true_stomach_acidities, t_intestine_lens, buffer_taro)
        p_len = engine.extract_plant_render_data(tree_grids, grass_grids, buffer_plants) # 🌟 NEW: 面のデータを抽出！
        m_len = engine.extract_active_coords(meat_x, meat_y, meat_active, buffer_meat)
        
        socketio.emit('taro_data', buffer_taro[:t_len].tobytes())
        socketio.emit('plant_data', buffer_plants[:p_len].tobytes()) # 🌟 名前を plant_data へ変更！
        socketio.emit('meat_data', buffer_meat[:m_len].tobytes())
        
        calc_time = time.time() - start_time
        
        if frame_count % 60 == 0:
            fps = 1.0 / calc_time if calc_time > 0 else 0
            alive_idx = np.where(taro_alive)[0]
            total_taro = len(alive_idx)
            
            if total_taro > 0:
                alive_fangs = t_fangs[alive_idx]
                herb = np.sum(alive_fangs <= 0.2)
                omni = np.sum((alive_fangs > 0.2) & (alive_fangs < 0.8))
                carni = np.sum(alive_fangs >= 0.8)
                print(f"⏱️ FPS:{fps:.0f} | 太郎:{total_taro}匹 (🌿草:{herb} 🥩雑:{omni} 🍖肉:{carni}) | 肉:{np.sum(meat_active)}")
                
                # 🌟 NEW: 死因レポートの出力
                d_age = death_stats[0]
                d_starve = death_stats[1]
                d_eaten = death_stats[2]
                total_deaths = d_age + d_starve + d_eaten
                avg_lifespan = death_stats[3] // total_deaths if total_deaths > 0 else 0
                
                
                print(f"   💀 死因レポート [直近60F] | 寿命:{d_age} 餓死:{d_starve} 被食:{d_eaten} | 死亡時平均年齢:{avg_lifespan}F")
                
                # 次の60フレームのためにリセット
                death_stats[:] = 0
            else:
                print(f"⏱️ FPS:{fps:.0f} | 太郎: 絶滅... | 肉:{np.sum(meat_active)}")
        if frame_count % 100 == 0:
            save_evolution_graph(taro_alive, t_fangs, t_intestine_lens, frame_count)
            save_stamina_graph(taro_alive, t_muscle_ratio, t_lung_capas, t_fangs, frame_count)
            save_digestion_graph(taro_alive, t_forestomach_capas, t_cecum_sizes, t_fangs, frame_count)
            save_microbiome_graph(taro_alive, t_microbiome, t_fangs, t_intestine_lens, frame_count)  # 🦠 NEW
            save_size_graph(taro_alive, t_sizes, t_speeds, t_fangs, frame_count)  # 🌟 NEW: サイズグラフ
            save_diet_histogram(taro_alive, t_fangs, t_intestine_lens, t_microbiome, frame_count)    # 📊 NEW
        socketio.sleep(max(0, 0.016 - calc_time))

# 🦠 NEW: 腸内細菌 vs 牙（食性との相関グラフ）
def save_microbiome_graph(taro_alive, t_microbiome, t_fangs, t_intestine_lens, frame_count):
    alive_idx = np.where(taro_alive)[0]
    if len(alive_idx) == 0: return

    # 腸の長さで色分け（長い腸=草食適応=緑、短い腸=肉食適応=赤）
    intestines = t_intestine_lens[alive_idx]
    colors = np.zeros((len(alive_idx), 4))
    for i, l in enumerate(intestines):
        # 腸が長いほど緑、短いほど赤
        colors[i] = [1.0 - l, l, 0.2, 0.5]

    plt.figure(figsize=(8, 6))
    sc = plt.scatter(t_fangs[alive_idx], t_microbiome[alive_idx], c=colors, s=15)
    plt.title(f"Microbiome vs Fangs (Frame: {frame_count} / Pop: {len(alive_idx)})")
    plt.xlabel("Fangs (0.0: Herbivore <---> 1.0: Carnivore)")
    plt.ylabel("Microbiome (腸内細菌定着度)")
    plt.xlim(-0.1, 1.1)
    plt.ylim(-0.05, 1.05)
    plt.axvline(x=0.2, color='green', linestyle='--', alpha=0.5, label='Herbivore')
    plt.axvline(x=0.8, color='red', linestyle='--', alpha=0.5, label='carnivorous')
    plt.legend(fontsize=8)
    plt.grid(True, linestyle='--', alpha=0.6)
    os.makedirs("graphs", exist_ok=True)
    plt.savefig("graphs/microbiome_latest.png")
    plt.close()

# 📊 NEW: 食性分布ヒストグラム（雑食が多いのか閾値の問題かを判断）
def save_diet_histogram(taro_alive, t_fangs, t_intestine_lens, t_microbiome, frame_count):
    alive_idx = np.where(taro_alive)[0]
    if len(alive_idx) == 0: return

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(f"Diet Distribution (Frame: {frame_count} / Pop: {len(alive_idx)})", fontsize=12)

    # 左: 牙の分布ヒストグラム
    axes[0].hist(t_fangs[alive_idx], bins=20, range=(0, 1), color='steelblue', edgecolor='black', alpha=0.7)
    axes[0].axvline(x=0.2, color='green', linestyle='--', label='Herbivore(0.2)')
    axes[0].axvline(x=0.8, color='red', linestyle='--', label='carnivorous(0.8)')
    axes[0].set_title("牙の分布（食性スペクトラム）")
    axes[0].set_xlabel("Fangs")
    axes[0].set_ylabel("Number of individuals")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.4)

    # 中: 腸の長さの分布
    axes[1].hist(t_intestine_lens[alive_idx], bins=20, range=(0, 1), color='mediumseagreen', edgecolor='black', alpha=0.7)
    axes[1].set_title("腸の長さの分布")
    axes[1].set_xlabel("Intestine Length (長い=草食適応)")
    axes[1].set_ylabel("Number of individuals")
    axes[1].grid(True, alpha=0.4)

    # 右: 腸内細菌の分布
    axes[2].hist(t_microbiome[alive_idx], bins=20, range=(0, 1), color='mediumpurple', edgecolor='black', alpha=0.7)
    axes[2].set_title("腸内細菌定着度の分布")
    axes[2].set_xlabel("Microbiome (0=なし, 1=定着)")
    axes[2].set_ylabel("Number of individuals")
    axes[2].grid(True, alpha=0.4)

    plt.tight_layout()
    os.makedirs("graphs", exist_ok=True)
    plt.savefig("graphs/diet_histogram_latest.png")
    plt.close()

if __name__ == '__main__':
    socketio.start_background_task(run_simulation)
    socketio.run(app, debug=True, use_reloader=False, port=5000, allow_unsafe_werkzeug=True)
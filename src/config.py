# ==========================================
# 🏢 config.py：宇宙の物理定数
# ==========================================
MAX_TARO = 30000
MAX_FOOD = 10000    
MAX_MEAT = 10000     
BASE_LIFESPAN = 3000      # 寿命の基準フレーム数
YEAR_LENGTH = 5000        # 🌟 NEW: 1年（季節が1周する）のフレーム数
WORLD_SIZE = 100.0  
GRID_SIZE = 50     

# 🌟 NEW: グリッドの物理サイズ（1マスあたりのサイズ）を定数化
GRID_SCALE = WORLD_SIZE / GRID_SIZE

# 🌏 地形生成パラメータ（Perlin Noise）
TERRAIN_SEED = 42          # 地形のシード（変えると別世界になる）
TERRAIN_SCALE = 8.0        # ノイズの空間スケール（大きいほど大きな地形特徴）
TERRAIN_OCTAVES = 4        # ノイズの重ね合わせ回数（多いほどディテール増加）
MOUNTAIN_THRESHOLD = 0.7   # この高度以上を「山」とする（描画用）
RIVER_THRESHOLD = 0.25     # この高度以下を「川/谷」とする
TEMP_ALTITUDE_FACTOR = 20.0  # 高度1.0あたりの気温低下（℃）
TEMP_BASE = 10.0              # 季節変動なしの基準気温
TEMP_SEASON_AMP = 15.0        # 季節変動の振幅（±15℃）
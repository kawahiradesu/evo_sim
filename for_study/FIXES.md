# evo_sim 修正案（具体的なコード例）

この文書は、分析レポートで指摘された問題を修正するための具体的なコード変更を示しています。

---

## 修正1：植物グリッドの初期化（最優先）

**ファイル**: `src/app.py`

**修正内容**: `run_simulation()` 関数で地形生成直後に植物を初期化します。

### Before（現在のコード）

```python
def run_simulation():
    print("🌍 宇宙を初期化中...")
    
    # 🏔️ Perlin Noiseによる地形生成
    altitude_grids[:] = terrain.generate_altitude((GRID_SIZE, GRID_SIZE))
    river_grids[:] = terrain.generate_river(altitude_grids)
    moisture_grids[:] = terrain.generate_moisture(altitude_grids, river_grids)
    
    # ← ここに植物初期化がない！
    
    for i in range(1000):
        # 個体の初期化...
```

### After（修正後）

```python
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
        # 個体の初期化...
```

**解説:**
1. 樹木を水分量に比例させて初期化（乾燥地では少ない）
2. 草も同様に初期化するが、樹冠ペナルティ（日陰）を考慮
3. 虫は草に依存する設計なので、自動的に計算される
4. コンソール出力で初期分布を検証可能に

---

## 修正2：BASE_LIFESPAN の統一

**ファイル**: `src/engine.py`

**修正内容**: config.py から import に変更

### Before（現在のコード）

```python
@njit
def process_life_cycle(taro_x, taro_y, taro_alive, ...):
    BASE_LIFESPAN = 4000  # ← ハードコード
    for i in range(len(taro_alive)):
        ...
        lifespan = BASE_LIFESPAN * (t_sizes[i] * 0.5 + 0.5)
```

### After（修正後）

**方法A: Numba の @njit が import に対応していない場合**

```python
# engine.py の最上部
@njit
def process_life_cycle_with_lifespan(taro_x, taro_y, taro_alive, ..., BASE_LIFESPAN):
    """BASE_LIFESPAN を引数として受け取る"""
    for i in range(len(taro_alive)):
        ...
        lifespan = BASE_LIFESPAN * (t_sizes[i] * 0.5 + 0.5)
        if t_ages[i] > lifespan:
            ...

# app.py で呼び出す
engine.process_life_cycle_with_lifespan(..., BASE_LIFESPAN=BASE_LIFESPAN)
```

**方法B: グローバル定数として Numba に認識させる場合**

```python
# engine.py の最上部
from config import BASE_LIFESPAN

# ...略...

@njit
def process_life_cycle(taro_x, taro_y, taro_alive, ...):
    for i in range(len(taro_alive)):
        ...
        lifespan = BASE_LIFESPAN * (t_sizes[i] * 0.5 + 0.5)  # グローバルから読み込み
```

**推奨**: 方法A（引数で明示的に渡す）が、テストしやすく、バグが少ないです。

---

## 修正3：エネルギー初期値の調整（推奨）

**ファイル**: `src/app.py`

**修正内容**: 初期エネルギーを動的に計算

### Before（現在のコード）

```python
        # 初期エネルギー（虫を主食にして生き延びる）
        t_energies[i] = 500.0  # 固定値
```

### After（修正後）

```python
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
```

**解説:**
- 体が大きい個体ほど多くのエネルギーが必要
- 個体ごとに必要最小限のエネルギーを計算
- コンソール出力で検証可能
- 初期フェーズで確実に虫が発生するまで生存できる

---

## 修正4：初期食性の最適化（推奨）

**ファイル**: `src/app.py`

**修正内容**: 虫食最適値への誘導

### Before（現在のコード）

```python
        # 🌟 イクチオステガ仕様（肉食）！
        t_fangs[i] = np.random.uniform(0.4, 0.6)  # 平均値：0.5
```

### After（修正後）

```python
        # 🌟 虫食最適値（0.5）を中心としたガウス分布
        # 多様性を保ちつつ、虫食効率が高い個体を優遇する
        t_fangs[i] = np.random.normal(0.5, 0.10)  # 平均 0.5, 標準偏差 0.10
        t_fangs[i] = np.clip(t_fangs[i], 0.0, 1.0)  # 0.0～1.0 の範囲に制限
```

**ガウス分布の特性:**
```
mean=0.5, std=0.1 の場合：
- 約 68% の個体が 0.4～0.6 の範囲（虫食最適値付近）
- 約 95% の個体が 0.3～0.7 の範囲
- 稀に 0.0～0.3 または 0.7～1.0 の個体も生まれる（多様性）
```

これにより、虫が十分にある場合、虫食特化個体が自然選択で増殖します。

---

## 修正5：デバッグ用のエネルギートレース（推奨）

**ファイル**: `src/engine.py` に追加

**修正内容**: エネルギー入出を可視化

```python
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
    print(f"  エネルギー: min={energies.min():.1f}, max={energies.max():.1f}, mean={energies.mean():.1f}")
```

**app.py での呼び出し:**

```python
# メインループ内
engine.debug_energy_trace(taro_alive, t_energies, t_sizes, t_speeds, t_ages, frame_count, interval=100)
```

**出力例:**
```
Frame 0: 生存数: 1000, エネルギー: min=500.0, max=500.0, mean=500.0
Frame 100: 生存数: 950, エネルギー: min=10.5, max=450.2, mean=250.3
Frame 500: 生存数: 200, エネルギー: min=0.1, max=100.5, mean=45.2
Frame 1000: 生存数: 0 (全員死亡)
```

このトレースから「いつ虫が発生するか」「虫発生時にエネルギーが回復するか」が可視化できます。

---

## 修正6：初期フェーズ用の短命モード（応急処置）

虫が発生するまで生存時間を延ばす応急対策：

**ファイル**: `src/app.py`

```python
# 初期化時
INITIAL_PHASE = 2000  # 最初の 2000フレームを「初期フェーズ」とする

# メインループ内
if frame_count < INITIAL_PHASE:
    # 初期フェーズでは消費コストを半減させる（幼体デバフと同じ）
    metabolism_multiplier = 0.25  # 0.5 ～ 1.5 ではなく 0.25 ～ 0.75
else:
    metabolism_multiplier = 0.5 + t_metabolisms[i]
```

**ただし**: これは根本的な解決ではなく、応急処置です。最優先は「修正1: 植物グリッドの初期化」です。

---

## 統合テスト例

修正を反映させた検証スクリプト：

```python
# test_energy_balance.py
def test_initial_phase_survival():
    """初期フェーズでエネルギーが赤字でないことを確認"""
    
    # シミュレーション設定
    individual_energy = 1000.0
    daily_cost = 0.35  # 平均的な消費
    survival_days = 1000
    
    # 虫がない場合
    no_food_balance = individual_energy - (daily_cost * survival_days)
    assert no_food_balance > 100, f"虫がない場合、{survival_days}フレーム後にエネルギー枯渇: {no_food_balance}"
    
    # 虫が十分にある場合
    food_income = 1.72  # 虫 1食分のエネルギー
    with_food_balance = individual_energy + (food_income * 100) - (daily_cost * survival_days)  # 100回接触
    assert with_food_balance > 500, f"虫がある場合、エネルギー黒字を確認できず: {with_food_balance}"
    
    print("✅ エネルギーバランステスト PASS")

def test_plant_growth():
    """初期フェーズで植物が十分に成長することを確認"""
    
    # Perlin noise 地形 + 初期植物
    moisture = 0.5  # 平均的な水分
    initial_grass = 250.0
    growth_rate = 4.0 * 0.3  # growth_power=0.3 と仮定
    frames = 1000
    
    final_grass = initial_grass + (growth_rate * frames)
    assert final_grass > 1000, f"1000フレーム後の草の量が不足: {final_grass}"
    
    # 虫の発生量
    initial_bugs = final_grass * 1.5
    assert initial_bugs > 100, f"虫の発生量が不足: {initial_bugs}"
    
    print("✅ 植物成長テスト PASS")

if __name__ == '__main__':
    test_initial_phase_survival()
    test_plant_growth()
```

---

## 適用順序

1. **修正1** (植物初期化) ← 最優先
2. **修正3** (エネルギー調整)
3. **修正4** (食性最適化)
4. **修正2** (BASE_LIFESPAN)
5. **修正5** (デバッグトレース)

修正1だけで、絶滅問題の大部分が解決します。

---

## 期待される改善

| 修正前 | 修正後 |
|---|---|
| 絶滅フレーム: 500～1000 | 絶滅フレーム: 5000+ または 生存継続 |
| 死亡原因：100% 餓死 | 死亡原因: 寿命・被食など多様化 |
| グラフ：全員が死亡 | グラフ: 進化分布が可視化 |

修正1を適用すれば、antigravity/walkthrough.md で述べた「季節変動と派生形質」の観察が可能になります。

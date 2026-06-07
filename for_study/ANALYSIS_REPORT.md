# 【evo_sim】設計と実装の齟齬分析 & 絶滅原因診断

コード設計の学習資料として、詳しく解説します。

---

## 📋 Executive Summary（執行サマリ）

**結論**: 絶滅の主原因は **エネルギー収支の深刻な不均衡** です。特に、初期フェーズで虫（bug_grids）が発生していないため、個体が何も食べられず飢餓死に至ります。

| 問題 | 深刻度 | 原因 |
|---|---|---|
| 虫が発生しない | 🔴 致命的 | 植物が初期化されていない（grass_grids が 0.0 で開始） |
| エネルギー消費が過剰 | 🔴 致命的 | 毎フレーム 0.1～5.0 程度のコストに対し、虫から得るエネルギーが不足 |
| BASE_LIFESPAN が異なる | 🟡 中 | config.py (3000) vs engine.py (4000) でハードコード |
| 食性スペクトラムが雑食中心 | 🟡 中 | 初期化で全員 fangs=0.4～0.6 に設定。虫中心設計と食い違い |
| 初期スタミナ設定が不適切 | 🟡 中 | max_staminas が 50.0～200.0 でばらつき大 |

---

## 🔍 詳細分析

### 【問題1】植物の初期化がない → 虫が発生しない → 食料源がない（致命的）

**SPEC に記載されていること：**
```
Layer 2: Ecological Layer（生態場）
- tree_grids ✅ — 木の密度
- grass_grids ✅ — 草の密度
- bug_grids ✅ — 虫の密度
```

**実装現状：**

[app.py](app.py#L250-L280) の `run_simulation()` 関数で初期化：
```python
# 🏔️ Perlin Noiseによる地形生成（terrain.py の関数を呼ぶ）
altitude_grids[:] = terrain.generate_altitude((GRID_SIZE, GRID_SIZE))
river_grids[:] = terrain.generate_river(altitude_grids)
moisture_grids[:] = terrain.generate_moisture(altitude_grids, river_grids)
```

**問題点：** `tree_grids` と `grass_grids` の初期化がない！

```python
# ❌ これがない！
# tree_grids[:] = initial_value  
# grass_grids[:] = initial_value
# bug_grids[:] = initial_value
```

**連鎖的な失敗：**

1. tree_grids = 0.0（初期値）
2. grass_grids = 0.0（初期値）
3. [engine.py#L268](engine.py#L268) の `process_bugs()` で：
   ```python
   bug_cap = (grass * 1.5) - (tree * 0.8)  # = (0.0 * 1.5) - (0.0 * 0.8) = 0.0
   ```
4. 結果：`bug_grids` も 0.0 で成長しない
5. 個体は虫を食べられない → エネルギー枯渇 → 絶滅

**設計の意図（SPEC より）：**
```
VERY_SLOWレイヤー (1000tick ごと):
【8】Layer 1: Terrain Update
    8a. moisture_grids を climate_phase に応じて更新
```

つまり、地形は**毎 1000フレーム更新される**という設計。しかし、**植物の初期値は決めていません**。

---

### 【問題2】エネルギー収支の根本的な不均衡

#### 2.1 毎フレームのエネルギー消費（process_life_cycle）

[engine.py#L684-L695](engine.py#L684-L695)：

```python
organ_cost = (actual_forestomach * 0.1) + (actual_cecum * 0.08) + (t_intestine_lens[i] * 0.05) + (t_true_stomach_acidities[i] * 0.02)
keratin_cost = t_keratins[i] * 0.1 * t_sizes[i]
nerve_cost = t_nerve_densities[i] * t_keratins[i] * 0.2 * t_sizes[i]

base_cost = 0.1 + ((t_sizes[i] ** 2) * 0.15) + (t_speeds[i] * 0.05) + organ_cost * 0.5 + keratin_cost + nerve_cost
metabolism_multiplier = 0.5 + t_metabolisms[i]  # 0.5 ~ 1.5 倍

t_energies[i] -= (base_cost * metabolism_multiplier)
```

**具体例：** サイズ 1.0, スピード 2.0, 代謝 0.5 の個体
```
base_cost = 0.1 + (1.0² × 0.15) + (2.0 × 0.05) + (0 × 0.5) + 0 + 0
         = 0.1 + 0.15 + 0.1
         = 0.35
t_energies[i] -= 0.35 × 1.0 = 0.35/フレーム
```

**1フレーム当たり最低 0.1, 平均 0.35～1.0 のエネルギー消費。**

#### 2.2 虫からのエネルギー獲得（process_bugs）

[engine.py#L244-L250](engine.py#L244-L250)：

```python
bug_tooth_score = max(0.1, 1.0 - abs(t_fangs[i] - 0.5) * 1.5)
carni_score = t_true_stomach_acidities[i] * bug_tooth_score
eat_amount = min(bug_grids[grid_y, grid_x], 2.0 + 3.0 * carni_score)
t_energies[i] += eat_amount * 0.4 * bug_tooth_score
```

**具体例：** fangs=0.5（最適な歯）, 胃酸=0.77 の虫食べ個体
```
bug_tooth_score = max(0.1, 1.0 - 0) = 1.0
carni_score = 0.77 × 1.0 = 0.77
eat_amount = min(bug_grids, 2.0 + 3.0 × 0.77) = min(bug_grids, 4.31)

# bug_grids に十分に虫がいると仮定：
t_energies[i] += 4.31 * 0.4 * 1.0 = +1.724 / 接触時
```

**しかし虫がいない場合：**
```
eat_amount = min(0, 4.31) = 0
t_energies[i] += 0  # 何ももらえない
```

#### 2.3 エネルギー収支の試算

| 時間軸 | 消費 | 獲得 | 収支 |
|---|---|---|---|
| 毎フレーム基本 | -0.35 | 0 | **-0.35** |
| 虫が十分にいる場合（接触時） | -0.35 | +1.724 | +1.374 |
| 虫がいない場合（初期フェーズ） | -0.35 | 0 | **-0.35** |

**結論：初期フェーズでは虫がゼロなので、個体は確実に餓死します。**

シミュレーション開始から 1000～5000 フレームで全員エネルギー枯渇。

---

### 【問題3】BASE_LIFESPAN のハードコード

**config.py:**
```python
BASE_LIFESPAN = 3000
```

**engine.py (line 669):**
```python
BASE_LIFESPAN = 4000  # ← ハードコード！
```

**設計の意図：**
SPEC_NEWed.MD の Table にて `BASE_LIFESPAN = 3000` と明示。しかし実装では 4000 で上書きされている。

**影響：**
- 老化死の判定が設計より 1000フレーム遅くなる
- 初期フェーズで虫がない場合、この差は関係ないが、長期安定性に影響する可能性あり

---

### 【問題4】初期化時の食性スペクトラムが広い

**app.py (line 297):**
```python
t_fangs[i] = np.random.uniform(0.4, 0.6)  # 全員が雑食中心
```

**SPEC の意図：**
```
虫の中心的な利用者は「歯の形が 0.5（円錐形）」の個体。
飛び抜けた胃酸と組み合わせることで虫食効率が最大化される。
```

**現状の問題：**
- 全員が 0.4～0.6 の「平凡な歯」でスタート
- 虫を食べるメリットがないので、進化圧が働かない
- 虫がいない状態ではなおさら進化不可能

**改善案：**
もし虫がいる環境なら、以下のような初期化が効果的：
```python
t_fangs[i] = np.random.normal(0.5, 0.1)  # 0.5 中心のガウス分布
```

---

### 【問題5】植物の成長が遅い（設計と実装の整合性）

**SPEC (process_plants より):**
```
【樹冠ペナルティ】木が300を超えると日陰になり始め、600で草は完全に育たなくなる
```

**実装 (engine.py line 36-50):**
```python
tree_grids[r, c] += 1.0 * growth_power  # 毎フレーム +1.0
grass_grids[r, c] += 4.0 * growth_power * (1.0 - shade_penalty)  # 毎フレーム +4.0
```

**問題分析：**

気温 15度、日照 0.6、水分 0.5 の「平均的な環境」と仮定：
```
growth_power = 0.5 × (15/15) × 0.6 = 0.3
tree_grids += 1.0 × 0.3 = +0.3/フレーム → 300 到達に 1000フレーム
grass_grids += 4.0 × 0.3 × 1.0 = +1.2/フレーム → 1000 到達に 833フレーム
```

**初期フェーズ（0-1000フレーム）で草が不足 → 虫が発生しない → 個体が飢える。**

---

### 【問題6】設計と実装の齟齬：虫食主義の矛盾

**SPEC より（walkthrough.md）：**
```
🌟 イクチオステガ仕様（肉食）！
虫を主食にして生き延びる
```

**app.py の初期化：**
```python
t_true_stomach_acidities[i] = 0.77  # 虫食効率を最大化する胃酸
t_forestomach_capas[i] = 0.0
t_cecum_sizes[i] = 0.0
t_intestine_lens[i] = 0.3            # 短腸（肉食型）
t_energies[i] = 500.0                # 初期エネルギー
```

**ただし虫がいない。** ← 最大の矛盾

これは、設計は「虫を主食にする環境」を想定していたが、実装では「虫の発生源（grass_grids）が初期化されていない」ため、虫が発生しない、という齟齬です。

---

## 🛠️ 根本原因の系統図

```
┌─────────────────────────────────────────────────────────┐
│ 根本原因：植物グリッド（tree_grids, grass_grids）が      │
│ 初期化されない                                           │
└─────────────────────────────────────────────────────────┘
                        ↓
         ┌──────────────┼──────────────┐
         ↓              ↓              ↓
   grass_grids     tree_grids     bug_grids
      = 0.0          = 0.0           = 0.0
         ↓
   虫が発生しない
   (bug_cap = grass × 1.5 - tree × 0.8 = 0)
         ↓
   個体が虫を食べられない
         ↓
   毎フレーム -0.35～-1.0 エネルギー消費
         ↓
   初期エネルギー 500.0 は
   1000～5000 フレームで枯渇
         ↓
    【全員餓死 → 絶滅】
```

---

## 📊 エネルギーフロー図（設計との比較）

### 設計では（SPEC より）

```
太陽（Layer 0）
    ↓
【植物成長】→ tree_grids, grass_grids
    ↓
【虫の発生】→ bug_grids（草に依存）
    ↓
【個体の食事】
 ├─ 虫を食べる
 ├─ 草を食べる
 └─ 肉を食べる（死骸）
    ↓
【個体のエネルギー維持】
    ↓
【死亡】→ 肉に変化（Layer 2 の土壌に戻る）
```

### 現実では（実装）

```
太陽（Layer 0）
    ↓
【植物成長】← ❌ 初期値ゼロ、成長遅い
    ↓
【虫の発生】← ❌ 草がないので虫がゼロ
    ↓
【個体の食事】
 ├─ ❌ 虫がない
 ├─ ❌ 草もない
 └─ ❌ 肉もない
    ↓
【個体のエネルギー維持】
    毎フレーム -0.35～-1.0
    ↓
【個体は 1000-5000 フレームで餓死】
    ↓
    全員死亡
```

---

## 🎓 教育的な設計の失敗パターン（コード設計演習）

このシミュレーションは、以下の設計教訓を学べます。

### ❌ 悪い設計パターン 1: 物理量の初期化を忘れる

```python
# ❌ 良くない例
tree_grids = np.zeros((GRID_SIZE, GRID_SIZE))  # 初期化後に値を入れない
grass_grids = np.zeros((GRID_SIZE, GRID_SIZE))
# シミュレーション開始
process_plants(tree_grids, grass_grids, ...)  # 最初のフレームで grass=0 のままで成長計算
```

**問題：** 最初のフレームで草の成長ができず、虫も発生しない。

**良い設計：**
```python
# ✅ 良い例
tree_grids = np.zeros((GRID_SIZE, GRID_SIZE))
grass_grids = np.random.uniform(50.0, 200.0, (GRID_SIZE, GRID_SIZE)) * moisture_grids
# または
grass_grids[:] = 100.0 * moisture_grids  # 水分に比例した初期草量
```

### ❌ 悪い設計パターン 2: エネルギー収支の計算を設計フェーズで行わない

設計者が「虫を食べるとエネルギー +1.7、毎フレーム消費 -0.35」という計算をしていれば、「虫がいない初期フェーズは 5000フレーム持たない」ことに気付けたはずです。

**良い設計：**
1. エネルギー消費の式を明示
2. エネルギー獲得の式を明示
3. 初期フェーズ（虫なし）での生存時間を計算
4. 必要なら初期エネルギーを調整

### ❌ 悪い設計パターン 3: ハードコードされた定数

```python
# ❌ 悪い例
BASE_LIFESPAN = 4000  # engine.py
BASE_LIFESPAN = 3000  # config.py
# どちらが本来の値なのか不明確
```

**良い設計：**
```python
# ✅ 良い例
# config.py で唯一定義
BASE_LIFESPAN = 3000

# engine.py で import
from config import BASE_LIFESPAN
```

### ❌ 悪い設計パターン 4: 設計ドキュメントと実装の乖離

**SPEC:** 「虫を主食にして生き延びる」
**実装:** 虫の発生源がない

この齟齬に気付くには、SPEC の「Layer 2」セクションを読んで「虫はどこから来るのか？」と逆算する必要があります。

---

## 💡 修正案（優先度順）

### 🔴 **【最優先】植物の初期化**

[app.py](app.py) の `run_simulation()` 関数に以下を追加：

```python
# 🌏 Perlin Noise による地形生成
altitude_grids[:] = terrain.generate_altitude((GRID_SIZE, GRID_SIZE))
river_grids[:] = terrain.generate_river(altitude_grids)
moisture_grids[:] = terrain.generate_moisture(altitude_grids, river_grids)

# 🌿 NEW: 植物の初期化（重要！）
tree_grids[:] = np.random.uniform(100.0, 300.0, (GRID_SIZE, GRID_SIZE)) * moisture_grids
grass_grids[:] = np.random.uniform(200.0, 500.0, (GRID_SIZE, GRID_SIZE)) * moisture_grids * (1.0 - (tree_grids / 600.0))
bug_grids[:] = (grass_grids * 1.5) - (tree_grids * 0.8)
bug_grids[:] = np.maximum(0.0, bug_grids)
```

**理由：** 虫が発生するために必須。これがないと個体は確実に餓死します。

### 🟡 **【重要】BASE_LIFESPAN の統一**

engine.py の line 669 を修正：
```python
# ❌ 現在
BASE_LIFESPAN = 4000

# ✅ 修正
from config import BASE_LIFESPAN  # import を使う
```

または

```python
# ✅ 修正（import 不可な場合）
BASE_LIFESPAN = 3000  # config.py と同じ値を使う
```

### 🟡 **【推奨】初期エネルギーの調整**

初期エネルギー 500.0 は十分でしょうか？

```
# 虫がいない初期フェーズ
消費: -0.35/フレーム × 500フレーム = -175 → 325 エネルギー残
消費: -0.35/フレーム × 1000フレーム = -350 → 150 エネルギー残
消費: -0.35/フレーム × 1500フレーム = -525 → -25 ← 絶滅

# 虫が発生し始める時刻（植物成長に 1000フレーム要）
その時点で既に虫が十分か不明確
```

**改善案：**
- 初期エネルギーを 1000～2000 に増やすか
- 初期フェーズの消費を減らすか（若い個体は消費を減らす）

### 🟡 **【検討】初期食性スペクトラムの調整**

全員を虫食（fangs ≈ 0.5）に特化させるか、多様性を保たせるか：

```python
# 🌟 多様性を保つ場合
t_fangs[i] = np.random.normal(0.5, 0.15)  # 0.5 中心ガウス分布
np.clip(t_fangs[i], 0.0, 1.0)

# 🌟 虫食効率を最大化する場合
t_fangs[i] = np.random.uniform(0.4, 0.6)  # そのまま（現状）
```

---

## 📚 参考資料との比較

### antigravity/walkthrough.md との関係

walkthrough.md は「Step 3: 季節変動と派生形質」での進捗を記録しています。

ここで追加されたのは：
- `t_metabolisms`: 基礎代謝
- `t_fat_ratios`: 脂肪蓄積率
- `t_keratins`: ケラチン量
- `t_keratin_types`: α/βケラチン系統
- `t_nerve_densities`: 神経密集度

**しかし、これらの機能は「虫が存在する環境」が前提です。** 虫がないと、これらの形質の進化圧も働きません。

---

## 📋 結論

| 項目 | 齟齬の有無 | 原因 | 深刻度 |
|---|---|---|---|
| エネルギーフロー（太陽→植物→虫→個体）| ✅ 齟齬あり | 植物の初期化漏れ | 🔴 致命的 |
| BASE_LIFESPAN の値 | ✅ 齟齬あり | ハードコード | 🟡 中 |
| 虫の発生メカニズム | ❌ 齟齬なし | 設計通りだが、入力（植物）がない | 🔴 致命的 |
| 個体の初期化 | ❌ 齟齬なし | 設計通り | 無 |
| 食性スペクトラム | ⚠️ 部分的 | 虫食最適値への誘導がない | 🟡 中 |

**絶滅の根本原因: 植物グリッドの初期化漏れにより、虫が発生しないため、個体が食料源を失う。**

---

## 🎯 コード設計の教訓

このシミュレーション開発を通じて学べることは：

1. **エネルギー保存則の検証が必須**
   - SPEC には「エネルギーの流れは閉じた系」とあるが、初期条件の検証が足りなかった

2. **Layer 間の依存関係を図で可視化すべき**
   - Layer 0 (気候) → Layer 1 (地形) → Layer 2 (植物・虫) → Layer 3 (個体)
   - 各 Layer の初期化をチェックリストとして管理

3. **単体テストの重要性**
   - `test_initial_energy_balance()`: 虫がない場合、個体は何フレーム生存できるか？
   - `test_plant_growth()`: 初期植物から虫が発生する時間を測定
   - `test_energy_flow()`: 1フレーム当たりのエネルギー出入りをログ

4. **ハードコード禁止**
   - すべての定数は config.py で管理し、import で使用

これは「シミュレーション開発の典型的な失敗」パターンです。設計段階で数値検証をしていれば防げた問題です。

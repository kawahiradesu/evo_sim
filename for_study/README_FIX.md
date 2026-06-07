# 【evo_sim】分析完了レポート 要点版

## 🎯 結論：絶滅の根本原因

**虫（bug_grids）が発生していない ← 植物グリッドが初期化されていないため**

```
┌─────────────────────────────┐
│ 植物グリッド（grass_grids）   │
│ が初期化されていない          │
│ 🔴 0.0 のまま開始             │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ 虫の発生条件:                │
│ bug_cap = grass × 1.5 - ...  │
│ = 0.0 × 1.5 - ...  = 0.0    │
│ 🔴 虫が発生しない             │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ 個体が虫を食べられない         │
│ 毎フレーム -0.35 消費         │
│ 獲得 = 0                     │
│ 🔴 初期エネルギー 500.0は     │
│    1000フレームで枯渇         │
└─────────────────────────────┘
              ↓
       【絶滅】
```

---

## 🔴 致命的な 2つの問題

### 問題1: 初期化漏れ

**app.py の `run_simulation()` で:**

```python
# 地形を生成するが...
altitude_grids[:] = terrain.generate_altitude((GRID_SIZE, GRID_SIZE))
river_grids[:] = terrain.generate_river(altitude_grids)
moisture_grids[:] = terrain.generate_moisture(altitude_grids, river_grids)

# ❌ 植物がない！
# tree_grids = 0.0
# grass_grids = 0.0
# → bug_grids = 0.0
```

### 問題2: エネルギー収支不均衡

| フェーズ | 消費/フレーム | 獲得/接触 | 生存時間 |
|---|---|---|---|
| 虫なし（現実） | -0.35 | 0 | **~1400フレーム** |
| 虫あり（本来） | -0.35 | +1.72 | ~無限 |

初期エネルギー 500.0 では、虫がない初期 1000 フレームを乗り切れません。

---

## 🛠️ 最小限の修正（3行追加）

**ファイル**: `src/app.py` 行番号 ~253

```python
def run_simulation():
    print("🌍 宇宙を初期化中...")
    
    # 🏔️ 地形生成
    altitude_grids[:] = terrain.generate_altitude((GRID_SIZE, GRID_SIZE))
    river_grids[:] = terrain.generate_river(altitude_grids)
    moisture_grids[:] = terrain.generate_moisture(altitude_grids, river_grids)
    
    # 🌿 NEW: ここに3行追加！
    tree_grids[:] = np.random.uniform(100.0, 300.0, (GRID_SIZE, GRID_SIZE)) * moisture_grids
    grass_grids[:] = np.random.uniform(200.0, 500.0, (GRID_SIZE, GRID_SIZE)) * moisture_grids
    bug_grids[:] = np.maximum(0.0, (grass_grids * 1.5) - (tree_grids * 0.8))
    
    for i in range(1000):
        # ...個体初期化...
```

**この 3行だけで、ほぼ全ての問題が解決します。**

---

## 📊 設計と実装の齟齬一覧

| 項目 | SPEC での定義 | 実装現状 | 結果 |
|---|---|---|---|
| **植物の初期状態** | 未指定（要推論） | 0.0 | 虫が発生しない ❌ |
| **虫の発生メカニズム** | Layer 2 で定義済 | 設計通り実装 | 植物がないので機能しない ❌ |
| **個体の食性** | 虫を主食 | fangs=0.4～0.6 | 虫がないので意味がない ❌ |
| **BASE_LIFESPAN** | 3000 (config.py) | 4000 (engine.py) | ハードコードで矛盾 |
| **初期エネルギー** | 未指定 | 500.0 固定 | 虫なしでは不足 |

---

## 🎓 この失敗から学べる教訓（コード設計の実践例）

### ❌ 悪い設計
```python
# Layer 間の依存関係が不明確
tree_grids = np.zeros(...)  # 何をする？
grass_grids = np.zeros(...) # 誰が初期化する？
bug_grids = np.zeros(...)   # どこから来る？
```

### ✅ 良い設計
```python
# Layer の依存関係を明確に

# Layer 1 (地形) → 初期化
altitude_grids[:] = generate_altitude(...)
moisture_grids[:] = generate_moisture(altitude_grids, ...)

# Layer 2 (植物・虫) → Layer 1 に依存して初期化
tree_grids[:] = initialize_trees(moisture_grids)
grass_grids[:] = initialize_grass(moisture_grids)
bug_grids[:] = initialize_bugs(grass_grids, tree_grids)

# Layer 3 (個体) → Layer 2 に依存して初期化
for i in range(MAX_TARO):
    taro_x[i], taro_y[i] = find_safe_spawn(river_grids, ...)
    t_energies[i] = calculate_survival_energy(BASE_LIFESPAN, ...)
```

---

## 📋 修正チェックリスト

- [ ] **最優先**: 植物グリッドの初期化を追加 (app.py ~253)
- [ ] **推奨**: 初期エネルギーを 1000～2000 に増加
- [ ] **推奨**: BASE_LIFESPAN を統一（config.py: 3000）
- [ ] **検討**: 初期食性を 0.5 中心のガウス分布に変更
- [ ] **デバッグ**: エネルギートレーススクリプトを追加

---

## 📁 関連ドキュメント

- **詳細分析**: [ANALYSIS_REPORT.md](ANALYSIS_REPORT.md) 
  - 全問題の詳細な図解と理由
  - コード設計の失敗パターン
  - 教育的な解説

- **修正コード例**: [FIXES.md](FIXES.md)
  - 6つの修正案の具体的なコード
  - Before / After の比較
  - テストコード例

- **設計仕様**: [SPEC_NEWed.MD](src/SPEC_NEWed.MD)
  - Layer 0-3 の階層設計
  - Update Pipeline（更新順序）

- **進捗参考**: [src/antigravity/walkthrough.md](src/antigravity/walkthrough.md)
  - Step 3 までの実装済み機能

---

## ✅ 検証方法

修正後、以下の点を確認してください：

```python
# コンソール出力で初期分布を確認
# 修正前: 虫密度が 0.0
# 修正後: 虫密度が 100～500 程度

# エネルギー推移を追跡
# 修正前: フレーム 0-1000 で全員 0 に
# 修正後: 虫食で回復、寿命まで生存

# グラフの進化を観察
# 修正前: 全員死亡で何も表示されない
# 修正後: 食性・体サイズなどの分布が可視化
```

---

## 💡 設計のポイント（今後の参考）

1. **エネルギー保存則を検証する**
   - 「閉じた系」と言ったら、数値で確認する
   - 初期条件 → 消費率 → 生存時間 を計算

2. **Layer 間の依存関係をチェックリスト化**
   - Layer 0 の初期化 ✓
   - Layer 1 の初期化 ✓
   - Layer 2 の初期化 ← **ここが抜けていた！**
   - Layer 3 の初期化 ✓

3. **単体テストで「虫が本当に発生するか」を確認**
   - シミュレーション開始直後に虫がゼロなら、何かが間違い

4. **ハードコードは絶対禁止**
   - BASE_LIFESPAN のような定数は config.py で一元管理
   - import で使用し、複数定義を防ぐ

---

## 🎯 次のステップ

1. 修正1（植物初期化）を適用
2. `python src/app.py` を実行して虫が発生するか確認
3. 個体が 1000フレーム以上生存するか確認
4. グラフに進化分布が表示されるか確認
5. 修正2～5 で細部を最適化

これで、antigravity/walkthrough.md で述べた「季節変動と派生形質の進化」が観察可能になります！

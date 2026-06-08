# 進化シム 修正ログ

> 各エントリの構成：診断・原因 / 設計理由 / コード差分 / 観察欄

---

## ログの凡例

| マーク | 意味 |
|---|---|
| 🔴 問題 | 観察された症状・バグ |
| 🔍 診断 | 原因の特定 |
| 💡 設計意図 | なぜこの変更か（生物学的・設計的根拠） |
| 📝 差分 | 変更前後のコード |
| 👁️ 観察 | 変更後の挙動メモ（後から記入） |

---

## #001 — 雑食無双・適者生存による絶滅

**日付：** 未記入  
**対象ファイル：** `engine.py`  
**症状：** 🔴 個体群が絶滅する。または雑食（t_fangs ≈ 0.5）が無双して多様性が失われる。

---

### 🔍 診断：原因は2つの構造的問題

**原因A：fermentation_bonus が臓器から独立している**

設計意図は「腸内細菌の絶対量に応じて草食個体が最大の利益を得る」だったが、実装では `t_microbiome`（菌の傾き比率）だけで発酵ボーナスが決まっていた。前胃・盲腸がなくても microbiome を草食菌寄りに保つだけで草食専門家とほぼ同等の収入が得られる。

数値検証（eat_amount=20、草食専門 vs 偽草食）：

| 個体 | base | fermentation | 合計 |
|---|---|---|---|
| 草食専門（臓器あり・菌あり） | 5.53 | 27.00 | 32.53 |
| 偽草食（臓器なし・菌だけ高い） | 0.68 | 27.00 | **27.68** |

臓器の有無で差が **5点しかない**。

```python
# process_interactions — 問題のある箇所
fermentation_bonus = eat_amount * t_microbiome[i] * 1.5
# t_microbiome は「傾き（比率）」であり「絶対量」ではない
# 臓器がなくても microbiome が同じなら発酵ボーナスはまったく同じになる
```

**原因B：fitness landscape に峰が1つしかない**

草と肉の消化効率式がそれぞれ「fangs=0 で最強」「fangs=1 で最強」のU字になっており、中間（fangs=0.5）が最も損をする構造。中間形質をフラットにすると今度は雑食が両方から利益を得て無双する。どちらに振っても多様性が維持されない。

```python
# 草：牙が0に近いほど有利
grass_penalty = max(0.01, 1.0 - t_fangs[i])

# 肉：牙が1に近いほど有利（二乗で急峻）
meat_efficiency = meat_organ_score * max(0.01, t_fangs[i] ** 2) * (3.0 + (t_fangs[i] * 3.0))
```

---

### 💡 設計意図：microbiome を「傾き」ではなく「絶対量」として機能させる

`t_microbiome` は 0.0〜1.0 の比率値（草食菌の優勢度）であり、菌の絶対数ではない。前胃・盲腸は菌が住める「家の広さ」を決める臓器として機能させることで、設計意図を式として表現する。

- `t_microbiome`：どちらの菌が優勢か（比率）
- `actual_forestomach + actual_cecum`：菌が定着できる最大量（容量）
- 両者の積 = 草食菌の実効的な絶対量

副次効果として「臓器を獲得してから菌が定着するまでタイムラグがある」という挙動が自然に生まれる（臓器あり・菌なし の個体は草からほとんど取れない）。

---

### 📝 差分

**`engine.py` — `process_interactions()`**

```python
# --- 変更前 ---
fermentation_bonus = eat_amount * t_microbiome[i] * 1.5

# --- 変更後 ---
# 前胃・盲腸 = 菌が住める家の広さ。臓器なしでは菌も少ししか定着できない
housing_capacity   = actual_forestomach + actual_cecum
fermentation_bonus = eat_amount * (t_microbiome[i] * housing_capacity) * 3.0
```

修正後の数値（eat_amount=20）：

| 個体 | base | fermentation | 合計 |
|---|---|---|---|
| 草食専門（臓器あり・菌あり） | 5.53 | 54.00 | **59.53** |
| 偽草食（臓器なし・菌だけ高い） | 0.68 | 10.80 | **11.48** |
| 雑食 | 2.22 | 24.00 | 26.22 |
| 肉食専門 | 0.14 | 1.20 | 1.34 |
| 臓器あり・菌なし | 4.30 | 6.00 | 10.30 |

草食専門 vs 偽草食の差：5点 → **48点**に拡大。

---

### 👁️ 観察（後から記入）

```
実施日：
生存フレーム数：
t_fangs 分布の変化：
death_stats の変化：
特記事項：
```

---

## #002 — コード構造リファクタリング

**日付：** 未記入  
**対象ファイル：** `engine.py`、`calc.py`（新規）、`test/test_calc.py`（新規）

---

### 💡 設計意図：数値計算層とロジック層の分離

**背景：** `engine.py` が700行超、10種類の責務が混在していた。可読性が低く、同じ計算が複数箇所に散在するリスクがあった。

**方針：**
- `calc.py`（新規）：副作用なしの純粋関数のみ。引数を受け取り数値を返す。テストしやすい。
- `engine.py`：ループ・判定・状態変更のみ。`calc.py` の関数を呼び出す。

**Numbaでの速度影響：** `@njit` 関数は呼び出し先を自動インライン展開するため、関数分割による速度低下はゼロ（500万回ループで誤差0.1ms以下を実測済み）。

---

### 📝 差分

**`calc.py`（新規作成）に抽出した関数一覧：**

| 関数 | 役割 |
|---|---|
| `calc_mass()` | 個体の総質量（size単位=m、イクチオステガ基準） |
| `calc_weight_penalty()` | 速度補正用の重さペナルティ |
| `calc_actual_organ_size()` | 臓器の物理制約（体の半分まで） |
| `calc_grass_efficiency()` | 草の消化効率 |
| `calc_fermentation_bonus()` | 発酵ボーナス（臓器依存・#001の修正を反映） |
| `calc_meat_efficiency()` | 肉の消化効率 |
| `calc_acid_penalty()` | 草食時の胃酸ペナルティ |
| `calc_bug_tooth_score()` | 虫を食べる歯のスコア |
| `calc_insulation()` | 断熱性（ケラチン種別） |
| `calc_cold_resistance()` | 総合寒冷耐性 |
| `calc_armor_value()` | 物理防御力 |
| `calc_damage_multiplier()` | 被ダメージ倍率 |
| `calc_genetic_distance()` | 遺伝的距離（繁殖互換性判定） |
| `calc_morpho_distance()` | 形態的距離（同種判定） |
| `calc_meat_yield()` | 倒したときの肉の量 |

**`engine.py` の構造変更：**

```python
# spawn_child()を分離（attempt_matingから66行を切り出し）
# 変更前：attempt_mating内にDNA生成が直接記述
# 変更後：
spawn_child(child_idx, i, j, ...)   # DNA生成専用
attempt_mating(...)                  # 繁殖判定のみ → spawn_childを呼ぶ

# attempt_combatに形態距離計算を移動
# 変更前：process_interactions側でM計算してis_same_speciesとして渡す
# 変更後：attempt_combat内部でcalc_morpho_distance()を呼ぶ

# get_genetic_distance/get_morpho_distanceを削除
# → calc.pyのcalc_genetic_distance/calc_morpho_distanceに統合
```

**単位系の確定（SPEC追記）：**

```
t_sizes 単位 = m（メートル）
初期値 1.0 = イクチオステガ基準（体長1m）
進化による上限は設けない（自然選択に委ねる）
```

**テスト（`test/test_calc.py`）：**

```
✅ calc_mass（4テスト）
✅ calc_grass_efficiency（3テスト）
✅ calc_fermentation_bonus（3テスト）
✅ calc_cold_resistance（4テスト）
✅ calc_armor_value（4テスト）
✅ calc_genetic_distance（3テスト）
✅ calc_morpho_distance（2テスト）
合計 23テスト、全パス
```

---

### 👁️ 観察（後から記入）

```
実施日：
リファクタリング前後でシムの挙動に変化があったか：
engine.pyの行数変化：
特記事項：
```

---

*— ログここまで —*
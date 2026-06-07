# Step 3: 季節変動と派生形質（Emergent Trait）

## 目的

これまで世界は「永遠の春」でしたが、ここに **Layer 0: Planetary Layer（気候・季節）** を導入します。
さらに、過酷な環境を生き延びるために仕様書 1.6 で定義された **Emergent Trait（派生形質）** を実装し、「複数の遺伝子の組み合わせで新しい能力が生まれる」創発的な進化を実現します。

## Proposed Changes

### 1. Layer 0: 気候フェーズの実装（`app.py` & `engine.py`）

世界に「季節のサイクル」を導入します。

- **`climate_phase` の導入**:
  - `0.0` 〜 `1.0` でループする進行度（1年 = 例: 5000フレーム）。
  - この進行度から、サイン波を使って **「グローバル気温（temperature）」** と **「日照量（sunlight）」** を計算します。
- **地形との連動**:
  - 標高（`altitude_grids`）が高い場所ほど気温が低くなるように補正をかけます（山の上の冬は凍えるほど寒い）。
- **植物への影響**:
  - `process_plants()` を更新し、日照量が減ると成長が止まり、気温が下がりすぎると枯れるようにします（冬枯れ）。

### 2. 個体の新遺伝子追加（`config.py` & `app.py`）

寒さや飢餓、そして外敵を乗り越えるための進化基盤として、以下の遺伝子を追加します。

- **`t_metabolisms`（基礎代謝）**:
  - 高い: 運動能力にボーナスがつくが、常に大量のエネルギーを消費する。
- **`t_fat_ratios`（脂肪蓄積率）**:
  - 高い: 余剰エネルギーを脂肪として蓄え、寒さ・飢えに強くなるが、体が重くなる。
- **`t_keratins`（ケラチン量）**:
  - 体表組織の多さ・厚さ。
- **`t_keratin_types`（ケラチン基底タイプ - 系統制約）**:
  - `0.0`: **α-ケラチン**（哺乳類系）- 柔軟で密。究極の保温（獣毛）を生むが、枝分かれ強度はない。
  - `1.0`: **β-ケラチン**（爬虫類/鳥類系）- 剛性が高い。硬い鎧（鱗）や枝分かれ構造（羽毛）を生む。
- **`t_keratin_complexities`（ケラチン構造の複雑さ）**:
  - `0.0`: 単純な管や平面。
  - `1.0`: フラクタルな枝分かれ構造。
- **`t_nerve_densities`（末梢神経密集度）**:
  - ケラチン根元の神経量。高いほど感覚が鋭くなるが維持コストが高い。

### 3. Emergent Trait（派生形質）の計算（`engine.py`）

遺伝子の**掛け算**で派生能力を動的に計算します。

```python
# ❄️ 寒冷耐性（Cold Resistance）
# 脂肪の量 + 獣毛(αケラチン × 単純構造) 
# または ダウン羽毛(βケラチン × 複雑構造)
alpha_fur_factor = (1.0 - t_keratin_types[i]) * (1.0 - t_keratin_complexities[i])
beta_down_factor = t_keratin_types[i] * t_keratin_complexities[i]
insulation = t_keratins[i] * max(alpha_fur_factor, beta_down_factor)

cold_resistance = (t_fat_ratios[i] * 0.5) + (insulation * 0.5)
```

```python
# 🛡️ 物理防御力（Armor）
# βケラチン × 単純構造(鱗)
scale_factor = t_keratin_types[i] * (1.0 - t_keratin_complexities[i])
armor_value = (t_keratins[i] * scale_factor) * (t_sizes[i] / 3.0)
```

```python
# 📡 感覚毛・センサー（Sensory Hair）
# ケラチン × 神経密集度
sensory_score = t_keratins[i] * t_nerve_densities[i]

# 夜間や森の中での視野ペナルティを軽減する
actual_vision = t_visions[i] * (0.5 + sensory_score * 0.5) # 例
```
# 気温が低いとき、寒冷耐性が足りないとエネルギーが急速に奪われる（凍死）
if local_temperature < 10.0:
    damage = (10.0 - local_temperature) * (1.0 - cold_resistance)
    t_energies[i] -= damage
```

```python
# 🛡️ 物理防御力（Armor）
# ケラチン(鱗に近いほど効果大) + サイズ
scale_factor = 1.0 - t_keratin_structs[i]  # 0.0で最大1.0
armor_value = (t_keratins[i] * scale_factor) * (t_sizes[i] / 3.0)

# 捕食された際のダメージを軽減
recoil = base_damage * (1.0 - armor_value * 0.5)
```

```python
# ⚖️ 体重ペナルティ（Weight Penalty）
# 脂肪と鱗は重く、スピードを低下させる
weight = (t_sizes[i] * 1.0) + (t_fat_ratios[i] * 0.5) + (t_keratins[i] * scale_factor * 0.5)
actual_speed = t_speeds[i] / max(1.0, weight)
```

## 期待される進化の創発

この実装により、場所と季節によって全く異なる生物が進化するはずです。

- **ジャングル（低地・常夏）**: 代謝が高く、脂肪が少なく、足が速い「全部乗せ」の競争社会。
- **ツンドラ・山頂（高地・極寒）**: 脂肪と**獣毛**を蓄え、冬を耐え抜く「マンモス」のような大型種。
- **激戦区の平原**: 肉食獣から身を守るため、**鱗の鎧**を身にまとった「アンキロサウルス」のような防御特化種。

---

## 変更対象ファイル

- **`config.py`**: 季節の周期（`YEAR_LENGTH`）、新遺伝子配列のMAX定義。
- **`app.py`**: 新遺伝子の配列宣言、初期化、バッファへの追加。季節の進行処理。
- **`engine.py`**: 
  - `process_plants()`: 気温・日照の影響追加。
  - `update_movement_and_stamina()`: 脂肪による速度ペナルティと寒冷ダメージ追加。
  - `process_life_cycle()`: 基礎代謝による常時エネルギー消費の追加。
  - 繁殖ロジックでの新遺伝子の交叉・変異。

## User Review Required

> [!IMPORTANT]
> **描画（フロントエンド）への反映について**
> 脂肪率や代謝をフロントエンド（色や形）に反映させることも可能です。例えば「脂肪率が高いと丸っこい（白っぽい）」「代謝が高いと赤っぽい」など。まずはシミュレーションの内部ロジックの実装を優先し、グラフ（`size_latest.png`など）で確認できるようにするか、画面上の見た目も同時に変えるか、ご希望はありますか？

## Verification Plan

- `climate_phase` が正しくループし、気温と日照が連動して変化するかをコンソール出力で確認。
- 冬に植物が減少し、草食動物が大量死（ボトルネック効果）するかを確認。
- `save_size_graph` や新規グラフで、世代を重ねるごとに「高地の生物」と「低地の生物」で脂肪率やサイズに差が出るかを観察。

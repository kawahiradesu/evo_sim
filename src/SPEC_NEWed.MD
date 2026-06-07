# Simulation SPEC v2
> 「生物を作る」のではなく「進化圧を作る」— 環境・エネルギー・相互作用から進化を創発させるシミュレーション

---

## Part 1: 設計思想

### 1.1 中心原則

このシミュレーションの個体は「最適化済みユニット」ではなく、「環境圧の結果として現れる存在」である。
進化はLayer 3の繁殖・突然変異の副産物として自然に創発する。Evolutionary Layerは独立して存在しない。

### 1.2 遺伝子と能力の関係

遺伝子は `0.0 ~ 1.0` の連続スペクトラムで管理する。現実の形質（目の位置・顎・腸・心臓・社会性）が連続的に変化するためである。

ただし能力は非線形である。「連続効果 + 閾値ボーナス」を採用する。

| 能力 | 非線形性 |
|---|---|
| 両眼視 | 視野重複で急激に距離感向上 |
| 飛行 | 翼・代謝・軽量化が揃う必要 |
| 草食 | 腸内細菌と長腸が必要 |
| 高知能 | 高代謝・神経容量が必要 |

完全な閾値にしない理由：中間形質を無価値にすると進化勾配が死ぬ。小さな羽は飛べなくても保温・バランス・ジャンプ補助に使える（Exaptation的進化）。

### 1.3 能力は掛け算で成立する

重要な能力は複数形質の相互依存で成立する。これにより系統制約・進化の袋小路・ニッチ分化が自然発生する。

```
flight = wing * metabolism * balance * muscle
```

### 1.4 全能力には必ずコストを持たせる

純粋上位互換は禁止。高性能器官はエネルギー消費・重量・発達コスト・環境依存性などの代償を持つ。「全部盛り万能生物」を防ぐ。

### 1.5 環境は固定ではない

環境は背景ではなく、生態系自身によって変化する。植物競争そのものが「進化圧生成装置」になる。バイオームは局所的に形成され、局所最適・隔離・種分化が発生しやすくなる。

### 1.6 エネルギー保存則

エネルギーの流れは閉じた系として設計する：

```
太陽（Layer 0）→ 植物（Layer 2）→ 動物（Layer 3）→ 死骸（Layer 2）→ 土壌（Layer 1）
```

エネルギーの発生源・消費先・循環を全レイヤーで一貫させる。

### 1.6 Emergent Trait（派生形質）

「Trait Unlock」は採用しない。時間ベースのUnlockは進化のレールを敷いてしまい、創発を殺す。

代わりに、高次能力は複数形質の連続値から計算される**派生値**として扱う。

# 飛行能力：掛け算で連続的に計算
# （βケラチン特化 * 構造の複雑さ * 筋肉 * 肺活量 / 体重）
# αケラチン系統（哺乳類）は強度不足で複雑な羽毛を作れないため、このルートでの飛行は極めて困難。
flight_score = (t_keratin_types * t_keratin_complexities) * t_muscle_ratio * t_lung_capas / (t_sizes + 0.1)

# 0.2 → 滑空補助
# 0.5 → 半飛行
# 0.8 → 真の飛行

# 🛡️ 体表の適応（ケラチンの派生と系統制約）
# ケラチンタイプ(α/β)と構造の複雑さで特性が分岐する。
# - 獣毛 (αケラチン特化): 柔軟で密。最高の寒冷耐性を持つが、枝分かれ（羽毛）にはなれない。
# - 鱗の鎧 (βケラチン特化・単純): 硬い防御力。重い。
# - 羽毛 (βケラチン特化・複雑): 枝分かれ構造。軽量保温・飛行能力の必須条件。
# 
# さらに末梢神経の密集度を掛けることで「センサー」となる：
# 感覚毛・気流センサー = t_keratins * t_nerve_densities
# 暗視能力や回避・飛行バランスにボーナスを与える。
```

これにより：
- 生化学的性質（αかβか）による**系統制約（Phylogenetic constraint）**が生まれ、哺乳類ルートと恐竜ルートが明確に分岐する。
- 羽毛と獣毛が混ざった不自然な生物は発生しない。
- 中間形質が無駄にならない（Exaptation / ex.感覚毛や保温用のダウンが将来の飛行に転用される）。
- どの系統が先に到達するかは世界次第
- 恐竜が知能を獲得する世界、飛行哺乳類が覇権を取る世界、など史実と異なる筋の通った世界が創発する

### 1.7 Update周期の分離

現象の更新頻度は「何桁遅いか」で設計する。厳密な時間対応より桁違いの時間差を作ることが創発に効く。

| 周期レベル | 倍率 | 対象 |
|---|---|---|
| FAST | 1tick | 移動・捕食・逃走・行動選択・エネルギー消費 |
| MEDIUM | 10tick | 植物成長・死骸腐敗・水分拡散・フェロモン・消化 |
| SLOW | 100tick | 繁殖・個体成熟・森林形成・草原化 |
| VERY_SLOW | 1000tick | 気候変動・季節・地形変化 |

**繁殖の例外：** 繁殖判定はSLOWだが、`t_cooldowns`のカウントダウンはFASTで毎tick行う。「繁殖できる状態かの監視」と「繁殖の実行」を分離する。

### 1.8 World Event（世界イベント）

イベントは**定期イベント**と**ランダムイベント**に分類する。

**定期イベント（世界の呼吸）：** `climate_phase` で管理し周期的にループする。

```
温暖期 → 冷涼期 → 氷河期 → 温暖期 → ...
```

これにより草原拡大・森林縮小・海面変化・動物の移動圧が定期的に発生する。

**ランダムイベント（World Events）：** 確率で発火する不可逆的な変動。

| イベント | 効果 |
|---|---|
| 隕石 | 広域ダメージ・日照低下 |
| 超火山 | 気温低下・植物枯死 |
| 大陸分断 TODO | 個体群の地理的隔離 |
| 植物革命 | 新植物種（突然変異ブースト）を出現させる |

**植物革命の設計方針：** 「被子植物を神が出す」のではなく「植物の大突然変異イベント」という枠だけ用意する。何が生まれるかは世界次第。結果として史実通りの被子植物革命も、超高速繁殖シダも、巨大菌類森林も起こりうる。

```python
WORLD_EVENT_PLANT_REVOLUTION = {
    "trigger": "random",
    "effect": "spawn_new_plant_variant",
    "mutation_boost": 3.0   # 植物の突然変異率を一時的に上昇
}
```

### 1.9 値の所有権原則

| 所有者 | 管理する値の種類 |
|---|---|
| Terrain Grid | 高度・水分・土壌栄養・温度 |
| Ecological Grid | 植物量・虫・死骸・病原菌・フェロモン |
| Entity | 遺伝子・状態・エネルギー・年齢 |
| Telemetry | 観測値（death_stats等）。どのレイヤーにも属さない |

個体は環境値を所有しない。グリッドが環境を所有し、個体はグリッドを読む。

---

## Part 2: レイヤー定義

### Layer 0: Planetary Layer（気候・季節）
世界の超大域を管理する。個体には直接作用せず、Layer 1〜2を通して間接的に影響する。

**管理する値：**
- 季節（0.0〜1.0 の周期）
- 平均気温オフセット
- CO2濃度（植物成長速度に影響）
- 大規模災害フラグ（隕石・火山・疫病）

**TODO:** 未実装。季節による moisture_grids の変動から着手予定。

---

### Layer 1: Terrain Layer（地形・地質）
固定寄りの地形情報を管理する。超低頻度で更新される。

**管理する値：**
- `moisture_grids` ✅ — 水分量（0.0: 砂漠 〜 1.0: オアシス）
- `altitude_grids` TODO — 高度（温度・水流・酸素・移動難易度を支配）
- `soil_grids` TODO — 土壌栄養（植物成長速度に影響）
- `river_grids` TODO — 河川（高所→低所へ流れる。侵食で谷・平野を形成）

**地形生成方針：** 完全なプレートシミュレーションではなく「進化圧を生む連続地形」を目指す。Perlin Noise / Simplex Noise / Ridged Noise を使用予定。

---

### Layer 2: Ecological Layer（生態場）
環境場を管理する。毎フレーム〜中頻度で更新される。

**管理する値：**
- `tree_grids` ✅ — 木の密度
- `grass_grids` ✅ — 草の密度
- `bug_grids` ✅ — 虫の密度
- `meat_x/y/amount/age` ✅ — 死骸（点データ）
- `pathogen_grids` TODO — 病原菌密度（密度依存イベントで使用）
- `pheromone_grids` TODO — フェロモン場

**植物競争：** 木と草が光獲得競争をする。木が300を超えると日陰ペナルティが発生し草が枯れる。この競争がバイオームを局所的に形成し、進化圧生成装置として機能する。

**密度依存イベント（MAX_TARO到達時）：**
個体密度が閾値を超えると以下のイベント発生確率が上昇する。MAX_TARO到達時は強制発火。

| イベント | メカニズム |
|---|---|
| 疫病 | `pathogen_grids` を通じて `t_microbiome` を逆用 |
| 植物枯渇 | `grass_grids` / `bug_grids` の再生速度を一時低下 |
| 飢餓連鎖 | `bug_grids` の供給量を激減 |

これは平時のランダムイベント（隕石・火山 = Layer 0）とは別レイヤーで管理する。

---

### Layer 3: Organism Layer（個体）
個体の状態と遺伝子を管理する。毎フレーム更新される。

#### 3.1 遺伝子（繁殖時のみ変化）

| 変数 | 意味 | 型 |
|---|---|---|
| `t_fangs` | 食性スペクトラム（0.0:草食 〜 1.0:肉食） | float32 |
| `t_sizes` | 体サイズ | float32 |
| `t_speeds` | 基礎移動速度 | float32 |
| `t_visions` | 視野半径 | float32 |
| `t_aggros` | 攻撃性 | float32 |
| `t_intels` | 知性 | float32 |
| `t_fears` | 恐怖感受性 | float32 |
| `t_true_stomach_acidities` | 胃酸強度 | float32 |
| `t_forestomach_capas` | 前胃容量（反芻型） | float32 |
| `t_cecum_sizes` | 盲腸サイズ（後腸発酵型） | float32 |
| `t_intestine_lens` | 腸の長さ | float32 |
| `t_muscle_ratio` | 筋肉タイプ（0.0:赤筋 〜 1.0:白筋） | float32 |
| `t_lung_capas` | 肺活量（スタミナ回復力） | float32 |
| `t_max_staminas` | スタミナ上限（タンク容量） | float32 |
| `t_metabolisms` | 基礎代謝（NEW: 高速移動/知性枠だが燃費悪化） | float32 |
| `t_fat_ratios` | 脂肪蓄積率（NEW: 飢餓・寒冷耐性だが重くなる） | float32 |
| `t_keratins` | ケラチン量（NEW: 体表の覆い。厚さ） | float32 |
| `t_keratin_types` | ケラチン基底タイプ（NEW: 0.0=α(柔軟/獣毛) 〜 1.0=β(剛性/鱗・羽毛)） | float32 |
| `t_keratin_complexities`| ケラチン構造の複雑さ（NEW: 0.0=単純な平面/管 〜 1.0=高度な枝分かれ） | float32 |
| `t_nerve_densities` | 末梢神経密集度（NEW: ケラチンと組み合わせて感覚毛に。脳コスト増） | float32 |

**`t_muscle_ratio` の設計方針：** 遺伝子として固定。訓練による個体差は `t_energies` / `t_staminas` の消費効率に吸収され、種の分化には寄与しないため状態値化しない。

#### 3.2 状態値（毎フレーム変化）

| 変数 | 意味 | 型 |
|---|---|---|
| `taro_x / taro_y` | 座標 | float32 |
| `taro_alive` | 生存フラグ | bool |
| `t_energies` | エネルギー残量 | float32 |
| `t_staminas` | スタミナ残量 | float32 |
| `t_current_speeds` | 現在出そうとしている速度 | float32 |
| `t_angles` | 向き | float32 |
| `t_ages` | 年齢（フレーム数）。リアル時間との対応は未定 TODO | int32 |
| `t_cooldowns` | 繁殖クールダウン | int32 |
| `t_microbiome` | 腸内細菌定着度（0.0:肉食菌 〜 1.0:草食菌） | float32 |

#### 3.3 寿命判定

`t_ages` が `BASE_LIFESPAN` を超えると確率的に死亡する。超過量が増えるほど死亡確率が上昇する（だんだん死ぬ）。

```python
if t_ages[i] > BASE_LIFESPAN:
    excess = t_ages[i] - BASE_LIFESPAN
    death_prob = min(1.0, excess / BASE_LIFESPAN)  # 超過100%で確率1.0
    if random() < death_prob:
        taro_alive[i] = False
```

`BASE_LIFESPAN` はグローバル定数。将来的に `t_sizes` に比例させ大型種ほど長命にする拡張を予定。

#### 3.4 幼体デバフ

誕生フレームから成熟年齢まで、全能力に成長係数をかける。

```python
maturity_age = BASE_LIFESPAN * 0.2 * t_sizes[i]  # 大型種ほど成熟が遅い
growth_factor = min(1.0, t_ages[i] / maturity_age)

actual_speed  = t_speeds[i]  * growth_factor
actual_vision = t_visions[i] * growth_factor
# 全能力に適用
```

#### 3.5 メモリ管理（スロット再利用）

`taro_alive == False` のスロットを子個体で上書きする。配列サイズは固定。MAX_TARO到達時は密度依存イベント（Layer 2）を強制発火させる。

---

### Telemetry（観測層）

レイヤーに属さない観測専用の値。シミュレーションの動作には影響しない。

| 変数 | 意味 |
|---|---|
| `death_stats` | 死因カウンタ（寿命・餓死・被食）+ 累計寿命 |

60フレームごとにリセットして出力する。

---

## Part 3: Update Pipeline（更新順序）

1フレームの処理順序。**この順序を変えると同フレーム依存バグが発生する。**

```
毎tick実行（FAST）:
【1】Layer 3: Organism Update — 空間グリッド構築
    1a. build_grids()                      # 衝突判定用グリッドを再構築

【2】Layer 3: Organism Update — AI・行動
    2a. update_ai_integrated()             # 視野・目標選択・角度決定

【3】Layer 3: Organism Update — 物理
    3a. update_movement_and_stamina()      # 移動・スタミナ消費・川ダメージ

【4】Layer 3: Organism Update — 相互作用
    4a. process_interactions()             # 捕食・繁殖・戦闘・草食・肉食

【5】Layer 3: Organism Update — 生命サイクル
    5a. process_life_cycle()               # 老化・餓死・臓器コスト・寿命判定
    5b. update_microbiome_survival()       # 腸内細菌のパッシブ変動

【6】Spawn Queue の処理
    - 前ステップで生まれた子個体を配列に書き込む
    TODO: 現状は attempt_mating 内で直接書き込み（要リファクタ）

10tickごと実行（MEDIUM）:
【7】Layer 2: Ecological Update
    7a. process_plants()                   # 木・草の成長（樹冠競争）
    7b. process_bugs()                     # 虫の発生（草・木に依存）
    7c. process_meat_decay()               # 死骸の腐敗
    7d. pathogen_spread()                  # 病原菌の拡散  TODO
    7e. density_event_check()              # 密度依存イベント判定  TODO

100tickごと実行（SLOW）:
    ※ 繁殖・成熟は個体の t_cooldowns / t_ages で管理。別途処理不要。

1000tickごと実行（VERY_SLOW）:
【8】Layer 1: Terrain Update
    8a. moisture_grids を climate_phase に応じて更新
    TODO: altitude / river / soil は未実装

【9】Layer 0: Planetary Update
    9a. climate_phase を進める（温暖期→冷涼期→氷河期→...）
    9b. World Eventの確率判定（隕石・火山・植物革命など）
    TODO: 未実装

毎tick実行（Telemetry & Render）:
【10】Telemetry
    - death_stats の集計・出力（60tickごと）
    - グラフ保存（100tickごと）

【11】Render
    - extract_taro_render_data()
    - extract_plant_render_data()
    - extract_active_coords()
    - socketio.emit()
```

---

## Part 4: 未解決・今後の設計課題

| 課題 | 優先度 | 備考 |
|---|---|---|
| 高度・地形生成（Perlin Noise） | 高 | 地形が進化圧の主要ドライバー。最優先 |
| エネルギー保存則の完全実装 | 高 | 植物の成長エネルギー源（太陽）が現状未定義 |
| Emergent Trait の派生値実装 | 高 | flight_score等の掛け算派生値。Google Antigravity着手前に設計を固める |
| pathogen_grids（密度依存疫病） | 中 | MAX_TARO問題の解決策 |
| 河川システム | 中 | 高度実装後に自然に続く |
| Layer 0（climate_phase・World Event） | 中 | VERY_SLOWレイヤー。moisture_gridsの季節変動から着手 |
| Spawn Queue のリファクタ | 低 | 現状動いているが設計上は分離すべき |
| t_ages のリアル時間対応 | 低 | フレーム数で管理は確定。リアル時間との対応は未定 |
| Google Antigravity を用いた実装 | 高 | コーディング支援ツールとして使用。SPEC完成後に本格着手 |
📜 SPEC.md: Taro Evolution Engine (Ichthyostega Edition)
1. Project Philosophy & Core Constraints (基本思想と制約)
本プロジェクトは「初期陸上脊椎動物の草食化プロセス」をシミュレートする人工生命エンジンである。
* Biological Realism over Engineering (生物学優先): 個体数制限などの工学的な強制終了（Culling）は行わない。個体群の増減は「環境収容力（リソースの供給量）」と「代謝コスト」による自然淘汰にのみ委ねる。
* Spectrum Mutation (連続的変異): 遺伝形質は基本的に float32 のスペクトラム（連続値）として表現し、世代交代時にガウス分布に基づく微小な変異（連続的変化）を与える。
* Data-Oriented Design (データ指向設計): 10万個体規模を維持するため、Pythonのクラス構造は排除し、全て Numpy の Structure of Arrays (SoA) と Numba (@njit) によるインプレース演算で実装する。
* Educational Documentation: 学習目的を兼ねるため、実装コードには「そのロジックが生物学的に何を意味しているか」を詳細にコメントアウトで記述する。
* **Non-linear Emergence (非線形な創発):** 遺伝子（DNA）は連続値のスペクトラムとして扱うが、それが発現する「能力・形質」は非線形（シグモイド的）に評価し、閾値を超えた際の「進化の革命」が自然発生する設計とする。

2. Memory Layout & Data Schema (メモリ・データ構造)
配列は全て1次元（1D Array）として初期化し、インデックス i が個体IDを意味する。最大確保数 MAX_TARO はメモリ確保用の上限であり、論理的な個体数制限には用いない。
2.1 Entity States (float32)
* Transform: taro_x, taro_y, t_angles (2次元座標と向き)
* Life Stats: taro_alive (bool_), t_energies (エネルギー), t_ages (int32, 寿命)
* Morphology (形質 - 長期的進化): t_sizes, t_fangs (牙の鋭さ), t_true_stomach_acidities (胃酸の強さ), t_intestine_lens (腸の長さ)
* Behavior (行動 - 中期的進化): t_speeds, t_aggros (攻撃性), t_fears (警戒心), t_visions (視界)
* Microbiome (細菌 - 短期的変化): t_microbiome (腸内細菌の定着度: 0.0~1.0)

* **Reserved Head Morphology (頭部の予約済み形質):**
  将来のアップデートで確実に追加される頭部・感覚器官のパラメータ枠（すべて 0.0 ~ 1.0 の float32）。
  * `t_brain_sizes` (脳容量), `t_eye_placements` (目の位置), `t_retina_types` (網膜細胞)
  * `t_olfactions` (嗅覚), `t_hearings` (聴覚), `t_echolocations` (反響定位)
  * `t_jaw_muscles` (顎の筋力), `t_jaw_lengths` (顎の長さ), `t_gapes` (口の可動域), `t_lips_vs_beaks` (唇と頬 vs 嘴)
  * `t_vocal_chords` (発声器官)

* **Reserved Torso & Organs (胴体・内臓の予約済み形質):**
  * `t_torso_lengths` (胴体の長さ), `t_torso_widths` (胴体の太さ), `t_neck_lengths` (首の長さ)
  * `t_liver_sizes` (肝臓の大きさ), `t_fat_ratios` (体脂肪率), `t_bone_marrows` (骨髄の充実度)
  * `t_heart_sizes` (心臓の大きさ), `t_heart_chambers` (心室の分離度: 0.0=2心房1心室 ~ 1.0=2心房2心室)
  * `t_pelvic_structures` (骨盤・肩帯の構造: 0.0=側方這い歩き/ガニ股 ~ 1.0=直立歩行)
* **Reserved Body & Integument (全身・外皮の予約済み形質):**
  * `t_armors` (皮膚の硬さ), `t_scaling_factors` (全身のアロメトリー係数)

* **Reserved Limbs (四肢の予約済み形質):**
  * 前肢・後肢は完全に独立したパラメータ（t_front_xxx, t_hind_xxx）として実装し、出力バランスは計算によって自然創発させる。
  * `t_front_femur_tibia` / `t_hind_femur_tibia` (大腿・脛骨比)
  * `t_front_foot_types` / `t_hind_foot_types` (接地形態: 0.0=ベタ足 ~ 1.0=ヒヅメ)
  * `t_front_dexterities` (前肢の器用さ: 手の進化用)
  * `t_webbed_feet` (水かき), `t_claws` (爪の鋭さ)

* **Reserved Tail (尾の予約済み形質):**
  * `t_tail_lengths` (尾の長さ/質量)
  * `t_tail_muscles` (尾の筋力/太さ)
  * `t_tail_flexibilities` (尾の柔軟性: 0.0=硬い棒 ~ 1.0=しなやかなムチ)
  * `t_tail_dexterities` (尾の把握能力: 0.0=ただの重り ~ 1.0=第5の手)
  * `t_tail_flatness` (尾の平坦さ: 0.0=円柱 ~ 1.0=平たいヒレ)
* **Reserved System-Wide Genetics (システム・全身の予約済み形質):**
  * `t_base_colors` (基本体色: 0.0=赤/砂漠適応 ~ 0.5=緑/ジャングル適応 ~ 1.0=黄茶/サバンナ適応)
  * `t_pattern_densities` (模様の濃さ: 0.0=無地 ~ 1.0=強烈な模様/分断迷彩)
  * `t_socialities` (社会性: 0.0=完全単独/縄張り ~ 1.0=巨大な群れ/スウォーム)
  * `t_clutch_sizes` (一度の産子数: 0.0=K戦略/1匹を確実に ~ 1.0=r戦略/多数をばら撒く)
  * `t_circadian_rhythms` (体内時計: 0.0=完全昼行性 ~ 1.0=完全夜行性)
2.2 Environment Grids (float32 / int32)
空間を分割し、O(1)の近傍探索を実現する。
* Bug Grids: bug_grids (2D) (各マスの虫の量。環境収容力のベース)
* Plant Grids: plant_grids (2D) (各マスの植物の量。石炭紀を想定し大量に発生)
* Spatial Index: t_counts, t_idx (3D) (各マスに存在する個体IDリスト)

3. Biological Heuristics (生物学ロジック実装定義)
3.1 Phase 1-2: Accidental Ingestion & Transmission (誤食と細菌定着)
* 誤食判定 (Accidental Ingestion):肉・虫を捕食するためにアクションを起こした際、対象の座標と同じグリッド内に植物が存在した場合、意図せず植物フラグを消費（摂食）してしまう処理を入れる。
* 細菌の垂直伝播 (Vertical Transmission):交尾・分裂による子孫生成時、子の初期 t_microbiome は親の値を引き継ぐ（卵表面への付着を表現）。t_microbiome[child] = t_microbiome[parent] + random_noise
* 環境伝播 (Environmental Transmission):一定確率で、排泄物として自身の居るグリッドに細菌スコアを散布し、他個体がそこを通過した際に感染するロジックを実装する（今後の拡張）。
3.2 Phase 3: Metabolic Reward & Behavior Shift (代謝報酬と行動変化)
* 行動バイアス (AI Targeting):update_ai_integrated 関数において、植物をターゲットとする魅力度（Score）の計算に t_microbiome を強い係数として乗算する。これにより、形質（腸の長さ等）が未発達でも、細菌さえ定着していれば「自発的に植物に向かう」行動が発現する。
* 消化効率 (Digestion Efficiency):植物を食べた際のエネルギー回復量は、「腸の長さ(プラス補正)」と「胃酸(マイナス補正)」に加え、「細菌量(強力なプラス補正)」の合成関数で決定する。
3.3 Phase 4-5: Mutation & Morphological Evolution (形質の進化)
* 繁殖時（attempt_mating）に、以下の処理を行う。
    1. 両親の形質（t_fangs, t_intestine_lens等）の平均値をとる。
    2. np.random.normal(0, scale)（ガウス分布）による微小なスペクトラム変異を加算する。
* 植物を食べる行動（行動バイアス）が定着した個体群は、植物からのエネルギー吸収効率を上げるために「長い腸」や「弱い胃酸」を持つ個体が生存に有利となり、世代を重ねるごとに形質がシフトしていく（自然淘汰）。
### 3.4 Reserved Biomechanics for Head (実装予約済みの頭部生体力学)
将来実装される頭部の各パラメータは、必ず強烈な「メリット」と「物理的コスト（トレードオフ）」を伴う。

* **脳と感覚器官 (Sensory & Intellect):**
  * `t_brain_sizes`: 高度な経路探索や記憶を可能にするが、基礎代謝（エネルギー消費）が極端に悪化する。
  * `t_eye_placements`: 側方眼(0.0)は奇襲を防ぐが狩りの命中率が落ち、前方眼(1.0)は狩りに特化するが横からの奇襲に弱い。
  * `t_retina_types`: 昼行性・色覚(0.0)と、夜行性・動体視力(1.0)のトレードオフ。
  * `t_olfactions` / `t_hearings`: 視界外の情報を得る強力なセンサーだが、情報過多による混乱やスタミナ回復遅延のデバフを伴う。
* **顎のテコと咀嚼 (Jaw Leverage & Chewing):**
  * `t_jaw_muscles` と `t_jaw_lengths` の物理演算（トルク）で実際の噛む力を算出。短く太い顎は骨砕き（ハイエナ）、長く細い顎はスピード特化（ワニ）となる。
  * `t_gapes`: 可動域が広い(1.0)と巨体を丸呑みできるが、消化中の移動速度に強烈なデバフがかかる（ヘビ）。
  * `t_lips_vs_beaks`: 唇(0.0)は「咀嚼」を可能にし草食のカロリー吸収率を爆増させる。嘴(1.0)は咀嚼できない代わりに頭部が劇的に軽くなり、移動時のスタミナ消費を抑える（鳥類）。
* **特殊器官 (Special Organs):**
  * `t_vocal_chords`: 威嚇や求愛に使えるが、スタミナを消費し天敵に位置を知らせる。
  * `t_echolocations`: 視界不良の環境を無効化する。第2のレーダーだが、声帯とセットで激しくスタミナを消費する。
  * **胴体のフォルムと首 (Torso & Neck):**
  * `t_torso_lengths` / `t_torso_widths`: 細長いと放熱性が高くジャングルに強いが内臓が小さくなる。太く短いと保温性が高く巨大な内臓を持てるが木に引っかかる。
  * `t_neck_lengths`: 長いと高所の草を食べられ俯瞰視界（バフ）を得るが、急所となり被ダメージが増加し心臓への負担も増える。
  * `t_pelvic_structures`: 側方這い歩き（0.0）は重心が低く隠密性が高いが、胴体をくねらせるため「走りながら呼吸できない（ダッシュ時スタミナ回復停止）」という制約を受ける。直立歩行（1.0）は走りながら呼吸できるが、バランスを維持するために脳や筋肉の基礎代謝コストが増大する。
* **代謝と免疫 (Metabolism & Immunity):**
  * `t_liver_sizes`: 毒素を無効化し一時的なエネルギーバッファとなるが、基礎代謝コストが跳ね上がる。
  * `t_fat_ratios`: 長期間の飢餓に耐え、装甲にもなるが、デッドウェイトとなり機動力が著しく低下する。
  * `t_bone_marrows`: 免疫力と血中酸素（スタミナ底上げ）のバフを与えるが、骨が中空ではなくなるため体重が激増する。
* **心臓の構造 (Heart Mechanics):**
  * `t_heart_sizes` と `t_heart_chambers`: 心臓が大きく心室が完全に分離（1.0）されているほど、圧倒的なスタミナ上限と回復力（高代謝・温血）を得るが、飢餓や寒冷に対する燃費が致命的に悪化する。2心房1心室（0.0）は持久力はないが省エネ（冷血）で生存できる。
* **全身・外皮 (Integument):**
  * `t_armors`: 被ダメージを割合でカットするが、重量増加と「放熱性の低下」による環境デバフを受ける。

* **脚の構造と接地 (Leg Structure & Foot Contact):**
  * `t_femur_tibia_ratios`: 脛骨が長いと跳躍力と最高速が伸びるが、重い体（高サイズや装甲）を支えられなくなる。
  * `t_foot_types`: ヒヅメ（1.0）は平地での最高速・燃費を極めるが、悪路（泥・ジャングル）で強烈な速度デバフを受ける。ベタ足（0.0）は安定し悪路に強い。
* **特殊器官と器用さ (Specialized Limbs & Dexterity):**
  * `t_webbed_feet`: 水辺（川）でのスタミナ減少・速度低下を無効化するが、陸上での歩行速度を著しく低下させる。
  * `t_limb_dexterities`: 神経が密集した「手」を持つと食事効率が上がり誤食を防ぐが、痛み（ダメージ時の恐怖心上昇）に極端に弱くなる。
  * `t_claws`: 攻撃力と地形走破性が上がるが、平地での燃費が悪化する。
* **尾の物理効果と水陸適応 (Tail Biomechanics & Aquatic Adaptation):**
  * `t_tail_lengths` / `t_tail_muscles`: 直立歩行（二足歩行）や高速跳躍時の「カウンターウェイト（バランサー）」として機能し、バランス崩壊による速度デバフを防ぐ。しかし質量が増えるため基礎代謝は悪化する。
  * `t_tail_flexibilities`: 硬い（0.0）と直立時の土台（カンガルー等）として安定し、しなやか（1.0）だとダッシュ中の急旋回デバフを軽減する（チーター等）。
  * `t_tail_dexterities`: 高いと「第5の手」として機能しジャングルの地形デバフを無視できるが、痛覚の増加（恐怖心デバフ）を伴う。
  * `t_tail_flatness`: 筋力と組み合わさることで水中（川）での圧倒的な推進力を生むが、陸上では空気抵抗と摩擦による強烈な速度デバフを受ける。
* **システムレベルの遺伝子と生存戦略 (System-Wide Genetics & Strategies):**
  * **迷彩と外見 (`t_base_colors`, `t_pattern_densities`):** 滞在している環境（バイオーム）と体色・模様が合致していると、他個体からの視認性が劇的に下がる（ステルスバフ）。逆に、ジャングル用の模様を持ったまま砂漠に出ると遠くからでも発見されやすくなる。
  * **社会性と群れ (`t_socialities`):** 群れることで恐怖心（`t_fears`）が和らぎ、集団で視界センサーを共有できるが、局所的なエサの枯渇速度が跳ね上がるため常に移動し続ける必要がある。
  * **繁殖戦略 (`t_clutch_sizes`):** 一度の出産で消費する親のエネルギーを「大きく強い少数」に割くか、「小さく弱い多数」にばら撒くか（r-K選択説）を決定する。
  * **活動サイクル (`t_circadian_rhythms`):** 将来実装される「昼夜のサイクル」において、活動時間に合致したタイミングで視界やスタミナ回復のバフを得るが、非活動時間はデバフを受ける（時間的すみわけの創発）。

### 3.5 Density-Dependent Events（密度依存イベント）
生きている個体数（alive_count）がMAX_TAROの閾値（例：90%）を
超えた場合、以下のイベントの発生確率が密度に比例して上昇する。
MAX_TARO到達時はこれらを強制発火させる（緊急フォールバック）。

- 疫病: t_microbiomeを逆用し、病原体として機能させる
- 植物枯渇: plant_gridsの再生速度を一時的に大幅低下
- 飢餓連鎖: bug_gridsの供給量を激減
### 3.6 Evolutionary Mechanics & Design Patterns (進化メカニクスと設計パターン)
多様な種分化とリアリティを生み出すため、パラメータの評価には以下の数学的・生態学的なデザインパターンを適用する。

* **二層構造と非線形バフ (Continuous & Threshold Effects):**
  形質は常に連続値だが、能力計算にはシグモイド関数等を適用し、「閾値未満でのわずかなバフ」と「閾値突破時の劇的な大バフ（革命）」の二層構造を作る（例：目が前方にある程度寄ると少し狩りが上手くなるが、閾値を超えると『完全な立体視』が開花する）。
* **能力の掛け算 (Multiplicative Synergies):**
  高度な能力（例：飛行、反芻など）は単一の遺伝子では成立せず、複数のパラメータの掛け算（例：`飛行スコア = 翼面積 * 筋力 * 骨の軽さ * 心室分離度`）で評価する。これにより、一極集中ではなくニッチな組み合わせを持つ種が自然発生しやすくなる。
* **外適応と進化の谷 (Exaptation & Evolutionary Valleys):**
  中途半端な形質が「完全な無駄（進化の谷）」にならないよう、複数の評価軸を持たせる。「飛ぶには短すぎる羽毛」であっても、別の計算式では「寒さデバフを軽減する保温材」として機能させることで、進化の足がかり（外適応）を作れるようにする。
* **総発達コストと万能防止 (Total Development Cost):**
  脳、高度な心臓、分厚い装甲などをすべて最大化すると、基礎代謝（`organ_cost`）がエネルギー摂取量を上回り、確定で餓死するバランスにする。これにより「すべてが最強の万能生物」の誕生を物理的に防ぐ。
* **形質解放フェーズ (Trait Unlocking):**
  シミュレーション初期（イクチオステガ時代）は、高度な遺伝子（完全な心室分離や高度な知能など）の変異をシステム的にロック（0.0で固定）しておく。フレーム数や特定の条件を満たしたタイミングでロックを解除し、段階的な「進化の爆発」を演出する。

4. Engine Pipeline (演算パイプライン)
メインループで呼び出される処理順序。
**時間スケール分離 (Time-Scale Separation):** 計算負荷の軽減とリアリティの追求のため、処理によって更新頻度を分ける（例：移動・衝突は毎フレーム、消化・代謝は10フレーム毎、植物の成長・生態系遷移は60フレーム毎など）。
graph TD
    A[Environment Update: 虫・植物の自然発生] --> B[Spatial Partition: グリッドインデックス構築]
    B --> C[AI Decision: 視野スキャン・報酬計算に基づく移動目標決定]
    C --> D[Movement: 座標更新]
    D --> E[Interaction: 接触・捕食・誤食判定]
    E --> F[Metabolism & Microbiome: 消化吸収・細菌の増減]
    F --> G[Life Cycle: 代謝コスト消費・寿命・繁殖判定]
G[Life Cycle] --> H[Spawn Queue の書き込み: 前フレームの子個体を配列に追加]

5. Coding Standards (コーディング規約)
1. Strict Typing: Numbaのコンパイルを最適化するため、配列の型（np.float32, np.int32）は厳密に一致させる。
2. Biological Commentary: コード内のコメントは「何を計算しているか」ではなく「なぜその計算になるか（生物学的な意図）」を記述する。
    * Bad: # 胃酸のマイナス乗算
    * Good: # 胃酸が強いと摂取した腸内細菌や植物の細胞壁が破壊され、共生発酵の効率が下がるためペナルティを与える
# 6. Future Ideas / Backlog (今後の拡張アイデア)
本セクションは、将来的なシミュレーションの高度化と、更なる多様性（種分化）の創出に向けたアイデアのストックである。

## 6.1 植物の生態遷移とバイオーム形成 (Flora Succession & Biomes)
* **スロット制による競争排他則 (Competitive Exclusion):**
  各グリッドに有限の「植物スロット（環境収容力の上限）」を持たせ、複数種の植物（木、草など）がスロットを奪い合うシステム。ある種がスロットを占有すると他種が侵入できなくなり、環境の均質化を防ぐ。
* **種子散布と空間的広がり (Seed Dispersal):**
  植物は基本的に「隣接するグリッド」へ転移して広がるロジックとする。スロット制と組み合わせることで、「深い森（ジャングル）」や「開けた草原」といった局所的な植生の偏り（パッチ）が自然形成され、グリッド内の植物比率がその土地の「環境（バイオーム）」を規定するようになる。
* **被子植物イベント (Angiosperm Revolution):**
  圧倒的な繁殖力と適応力を持つ「被子植物（花や広葉樹）」がランダムなタイミング・場所で発生するイベント。既存の植物スロットを次々と奪い取り、世界中の風景を一変させる（白亜紀の陸上革命の再現）。

## 6.2 地形と環境パラメータの拡張 (Terrain & Environmental Factors)
* **局所的な環境勾配 (Nutrients & Moisture Gradient):**
  グリッドごとに「水分量」や「土壌栄養度」などの静的/動的なパラメータを持たせる。これにより、水分が枯渇した場所には「砂漠」が自然発生し、植物の生え方（オアシスや不毛の地）に明確な地域差が生まれる。
* **物理的な地形の導入 (Topological Features):**
  「穴」や「段差」などの地形的特徴をグリッドに付与する。これらは外敵から身を隠すシェルター（巣）として機能したり、移動を阻む物理的な壁（隔離要因）となったりすることで、新たな生存戦略（ニッチの細分化）を促す。
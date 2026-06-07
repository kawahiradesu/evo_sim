import pygame
import sys
# 修正前：from individual import Individual
# 修正後：entities フォルダを指定する
from evo_sim.archive_v1.entities.individual import Individual
# environment.py も、もしファイル名が 'enviroment.py' なら名前に合わせます
# スペルミス（nが抜けている）に注意！画像では enviroment.py になっていますね。
from evo_sim.archive_v1.environment.swamp import Swamp 
import random

marsh = Swamp()
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 30 #1秒間に何回更新するか

#pygame本体の初期化
pygame.init()


#実際に窓を作る
#screenという変数にキャンパスを代入する
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("デボン紀進化シミュレーター")

font = pygame.font.SysFont(None, 24)
#時間を管理する
clock = pygame.time.Clock()

COLOR_SWAMP =(30, 60, 50) #深緑色の沼
COLOR_TARO = (100, 200 , 100)

#ロジック
def next_generation(survivors, population_size):
    """
    生き残った個体からオスとメスを分けて次世代を作る。
    """
    males = [ind for ind in survivors if ind.gender == "Male"]
    females = [ind for ind in survivors if ind.gender =="Female"]

    next_gen = []

    #オスとメスがいないなら繁殖できない。
    if not males or not females:
        return[]
    
    #リストをシャッフルしてランダムな出会いを演出
    random.shuffle(males)
    random.shuffle(females)

    #少ない方の性別の数だけペアが生まれる
    num_pairs = min(len(males),len(females))

    #次の世代の個体数を維持するために、１ペアから何びき生まれるか計算
    #例：個体数10を維持したいなら、1ペアあたり（10/ペア数）必要
    children_per_pair = max(2,population_size//num_pairs)

    for i in range (num_pairs):
        """
        両親の形質を受け継ぐ
        """
        papa = males[i]
        mama = females[i]

        #魅力度(今は画一的に0.5。後で形質と連動）
        #aoeel = (papa.appeal + mama.appeal)

        for _ in range(children_per_pair):
            if len(next_gen) >= population_size:
                break

            #新しい個体を作成
            child = Individual(individual_id=random.randint(1000,9999))
            
            child.crossover(papa,mama)
            #親のステータスをコピーする処理が必要。
            #ここでは簡単のためそのままmutateさせる。
            child.mutate()
            next_gen.append(child)

    return next_gen


population_size = 50
#population_sizeの数だけ個体を作成
population = [Individual(i) for i in range(population_size)]

#100世代まで
# main.py のループ部分

for generation in range(1, 100):
    print(f"--- 第{generation}世代 観察開始 ---")
    #資源のリセット
    marsh.insect_stock = 1000
    marsh.fish_stock = 1000
    for frame in range(600):
        marsh.insect_stock =min(1200, marsh.insect_stock + 2)
        marsh.fish_stock = min(1200, marsh.fish_stock + 2)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        
        # --- 1. まず背景を塗る（一番奥） ---
        screen.fill(marsh.land_color) # 陸地
        pygame.draw.rect(screen, marsh.water_color, (0, marsh.water_y_line, 1200, 800 - marsh.water_y_line)) # 水域

        #個体の計算と描写を一つにまとめる
        # 個体の計算と描画
        for i, ind in enumerate(population): # enumerateを使うとインデックス(i)が取れて便利だじょ
            ind.move(marsh)
            ind.eat(marsh)

            if ind.eat_effect_timer > 0:
                ind.eat_effect_timer -= 1
            # 描画するのは最初の50匹だけ（重さ対策）
            if i < 50:
                pos = (int(ind.pos.x), int(ind.pos.y))
                
                # 1. 基本の色とサイズを決定
                if ind.hydration < 0.3:
                    taro_color = (240, 240, 255) # 脱水：青白い
                else:
                    taro_color = (100, 200, 100) # 健康：緑
                
                size = 3 + int(ind.energy / 20) # エネルギー量で太さが変わる！

                # 2. 食事エフェクトの判定
                if ind.eat_effect_timer > 0:
                    # 食べた瞬間は黄色く光る（少し大きめに描画）
                    pygame.draw.circle(screen, (255, 255, 0), pos, size + 4)
                    ind.eat_effect_timer -= 1 
                
                # 3. 本体を描画
                pygame.draw.circle(screen, taro_color, pos, size)

        # 在庫表示（フォントの設定はループの外で1回やるのがおすすめだじょ）
        insect_text = font.render(f"Insects: {marsh.insect_stock}", True, (200, 200, 200))
        fish_text = font.render(f"Fish: {marsh.fish_stock}", True, (200, 200, 200))
        screen.blit(insect_text, (20, 20))
        screen.blit(fish_text, (20, 50))
        # --- ここを追加！ ---
        pygame.display.flip()  # 描いたものを画面に反映させる
        clock.tick(FPS)        # 速度を一定に保つ

    print(f"--- 第{generation}世代 判定フェーズへ ---")
    
    # 生存判定
    survivors = []
    for ind in population:
        score = marsh.evaluate(ind)
        if random.random() <= score:
            survivors.append(ind)
            
    # 繁殖
    population = next_generation(survivors, population_size)
    if not population: break
import matplotlib.pyplot as plt
import pandas as pd

# --- 1. 最終世代のデータを集計 ---
data = []
# Swampのインスタンス（評価関数を持っているオブジェクト）が必要
# 変数名がenvやswampなど、あなたのmain.pyでの定義に合わせて変えてください
env = Swamp() 

for ind in population:
    data.append({
        "body_height": ind.front_body_height,
        "fitness": env.evaluate(ind),  # ここで実際の適応度（スコア）を取得
        "weight": ind.total_weight,
        "shoulder_angle": ind.sholder.front_join_angle,
        "knee_v": ind.front_leg.knee_angle_vertical,
        "torso_width": ind.torso.width
    })

df = pd.DataFrame(data)

print(df.columns)
print(df.head())
print(population[0].__dict__)

# --- 2. 散布図の作成 ---
plt.figure(figsize=(10, 6))
# Y軸を speed から fitness に変更
plt.scatter(df["body_weight"], df["fitness"], alpha=0.5, c=df["weight"], cmap='viridis')
plt.colorbar(label="Total Weight")
plt.title("Evolution Result: Body Height vs Fitness")
plt.xlabel("Body Height (Clearance from ground)")
plt.ylabel("Fitness (Success Score)")
# 画像を保存する
plt.savefig("evolution_scatter.png")

# 【ここを追加！】実行時に画面に表示させる
plt.show()
# --- 3. 詳細な形質レポートの拡張 ---
print("\n" + "="*40)
print(" 🧬 最終世代：詳細形質分析レポート ")
print("="*40)

def avg(key):
    # ネストされた構造から平均値を出すためのヘルパー
    if "knee" in key: return sum(getattr(p.front_leg, key) for p in population) / len(population)
    if "torso" in key: return sum(getattr(p.torso, key.replace("torso_","")) for p in population) / len(population)
    if "sholder" in key: return sum(p.sholder.front_join_angle for p in population) / len(population)
    return 0

print(f"【体幹】長さ: {avg('torso_length'):.3f} | 幅: {avg('torso_width'):.3f} | 柔軟性: {avg('torso_flexibility'):.3f}")
print(f"【生え際】肩の角度(1.0=直立): {avg('sholder'):.3f}")
print(f"【関節】膝(垂直): {avg('knee_angle_vertical'):.3f} | 膝(水平): {avg('knee_angle_horizontal'):.3f}")
print(f"【前脚部】上腕長: {sum(p.front_leg.up_leg.length for p in population)/len(population):.3f} | 下腕長: {sum(p.front_leg.low_leg.length for p in population)/len(population):.3f}")
print(f"【後脚部】上腕長: {sum(p.back_leg.up_leg.length for p in population)/len(population):.3f} | 下腕長: {sum(p.back_leg.low_leg.length for p in population)/len(population):.3f}")
# レポート出力部分に追加
print(f"【体幹】長さ: {avg('torso_length'):.3f} | 幅: {avg('torso_width'):.3f} | 柔軟性: {avg('torso_flexibility'):.3f}")
# 骨盤（Pelvis）の進化も気になるじょ！
print(f"【生え際】肩角度: {avg('sholder'):.3f} | 腰角度(1.0=直立): {sum(p.pelvis.hip_joint_angle for p in population)/len(population):.3f}")
print("-" * 40)
print(df.columns)
print(df.head())
print(population[0].__dict__)
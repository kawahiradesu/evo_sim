import random
from individual import Indevidual
from genome import Genome

def run_ecosystem_demo():
    print("🌍 --- 創世記：太郎のデスゲームが始まる --- 🌍")

    base_taro_dna = Genome(parent_dna = None).dna
    #1.10匹の太郎を生成する。
    population = []
    for i in range(10):
        #個体ごとに少しずつ内臓の重さが違う!
        taro = Indevidual(parent_dna=base_taro_dna)

        taro.energy = 100.0
        population.append(taro)

    #最初は全員生きてる
    day = 1

    #サバイバルループ
    while len(population) > 0 and day <= 10:
        print(f"\n🌅 【{day}日目】 生存者: {len(population)}匹")

        survivors = []
        for i , taro in enumerate(population):
            #毎日の餌探し
            found_food = random.uniform(10.0,20.0)
            taro.energy += found_food

            #基礎代謝の消費
            taro.consume_energy()

            if taro.is_alive:
                survivors.append(taro)
                print(f"  生き残り {i}号 | 燃費: {taro.dialy_cost:.1f} | 残りHP: {taro.energy:.1f}")
            else:
                print(f"  💀 {i}号が餓死... (高燃費: {taro.dialy_cost:.1f} が仇となった)")
            
            #生き残った個体だけで次の日へ
        population = survivors
        day += 1
        
    print("\n🏁 --- デスゲーム終了 --- 🏁")
    if len(population) > 0:
        print(f"🎉 {len(population)}匹が生き延びた！低燃費の勝利だ！")
    else:
        print("💀 全滅... 環境のエサが少なすぎた！")

if __name__ == "__main__":
    run_ecosystem_demo()
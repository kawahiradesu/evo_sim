import traits_calc

def test_metabolism():
    taro_dna = {'head_scale': 0.4, 'liver_size':0.3}
    base_cost = traits_calc.cale_base_metabolism(taro_dna)

    monster_dna = {'head_scale': 0.4, 'liver_size': 1.0}
    monster_cost = traits_calc.cale_base_metabolism(monster_dna)
    
    assert monster_cost > base_cost,"エラーだよ！肝臓がでかいのに燃費がいいのわけわからん"
    
    #ファイルセーフのテスと{最小の時}
    tiny_dna = {'head_scale': 0.0, 'liver_size': 0.0,
        'jaw_muscle_mass': 0.0, 'heart_muscle': 0.0,
        'stomach_compartments': 0.0, 'intestine_length': 0.0,
        'fat_distribution': 0.0}
    tiny_cost = traits_calc.cale_base_metabolism(tiny_dna)
    assert tiny_cost == 5.0,"エラー！！最低限のカロリー消費はどこいった？"

    print("代謝テスト完了！！！")

test_metabolism()
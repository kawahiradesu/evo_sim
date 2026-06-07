import numpy as np

def build_dod_arrays(population):
    """
    世界構築エンジン
    1000匹のoopの太郎たちから、毎フレーム描画に必要なステータスだけを抽出して
    DODに変換する魔法の関数
    """
    num_entities = len(population)

    #1.空のスプレットシート
    #np.zerosは「全部ゼロで埋まったリスト」を高速で作る関数。
    x_positions = np.zeros(num_entities)
    y_positions = np.zeros(num_entities)
    speeds      = np.zeros(num_entities)
    angles       = np.zeros(num_entities)
    visions     = np.zeros(num_entities)

    #2.oopの太郎たちからデータを吸い出してスプレッドシートに書き込む
    for i, taro in enumerate(population):
        x_positions[i] = taro.x
        y_positions[i] = taro.y
        speeds[i]      = taro.speed
        angles[i]       = taro.facing_angle
        visions[i]     = taro.vision_range

    #これで「抽象パーツ」の完成
    return x_positions, y_positions, speeds, angles, visions

def update_movement_system(x_positions, y_positions, speeds, angle):
    """
    [移動システム]
    for文は不要!!
    NumPyの魔法(ベクトル演算)で、10万匹の座標を更新する!!
    """
    #ここからがDODの魔法！
    x_positions += np.cos(angle) * speeds
    y_positions += np.sin(angle) * speeds

    return x_positions, y_positions

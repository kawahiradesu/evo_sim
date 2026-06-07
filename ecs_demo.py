import numpy as np
import random
import time
from numba import njit

# --- 🏢 宇宙の物理定数 ---
MAX_TARO = 30000    
MAX_FOOD = 100000   
WORLD_SIZE = 100.0  

# --- 🌱 Numba：植物の自動再生 ---
@njit
def spawn_food(food_x, food_y, food_active, amount):
    spawned = 0
    for i in range(MAX_FOOD):
        if not food_active[i]:
            food_active[i] = True
            food_x[i] = random.uniform(0, WORLD_SIZE)
            food_y[i] = random.uniform(0, WORLD_SIZE)
            spawned += 1
            if spawned >= amount:
                break

# --- 🧱 Numba：エサをマンション（グリッド）に仕分ける ---
@njit
def build_food_grid(food_x, food_y, food_active, grid_counts, grid_indices):
    grid_counts[:] = 0 
    
    for i in range(MAX_FOOD):
        if not food_active[i]:
            continue
        gx = int(food_x[i] / (WORLD_SIZE / 10.0))
        gy = int(food_y[i] / (WORLD_SIZE / 10.0))
        gx = max(0, min(gx, 9))
        gy = max(0, min(gy, 9))

        count = grid_counts[gx, gy]
        if count < 500:
            grid_indices[gx, gy, count] = i
            grid_counts[gx, gy] += 1

# --- 🧠 Numba：爆速索敵 ---
@njit
def update_ai_vision_grid(taro_x, taro_y, taro_alive, food_x, food_y, grid_counts, grid_indices, visions, taro_angles):
    for i in range(MAX_TARO):
        if not taro_alive[i]: 
            continue

        tx, ty = taro_x[i], taro_y[i]
        gx, gy = int(tx / (WORLD_SIZE / 10.0)), int(ty / (WORLD_SIZE / 10.0))
        gx = max(0, min(gx, 9)); gy = max(0, min(gy, 9))

        min_dist_sq = visions[i] ** 2 
        best_food_idx = -1

        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < 10 and 0 <= ny < 10:
                    count = grid_counts[nx, ny]
                    for c in range(count):
                        f_idx = grid_indices[nx, ny, c]
                        dist_sq = (food_x[f_idx] - tx)**2 + (food_y[f_idx] - ty)**2
                        if dist_sq < min_dist_sq:
                            min_dist_sq = dist_sq
                            best_food_idx = f_idx

        if best_food_idx != -1:
            taro_angles[i] = np.arctan2(food_y[best_food_idx] - ty, food_x[best_food_idx] - tx)
        else:
            taro_angles[i] = taro_angles[i] + (random.random() * 0.4 - 0.2)

# --- 🍖 Numba：摂食システム ---
@njit
def process_eating(taro_x, taro_y, taro_alive, taro_energies, food_x, food_y, food_active, grid_counts, grid_indices):
    eat_dist_sq = 2.0 * 2.0
    for i in range(MAX_TARO):
        if not taro_alive[i]: continue

        tx, ty = taro_x[i], taro_y[i]
        gx, gy = int(tx / (WORLD_SIZE / 10.0)), int(ty / (WORLD_SIZE / 10.0))
        gx = max(0, min(gx, 9)); gy = max(0, min(gy, 9))

        eaten = False
        for dx in range(-1, 2):
            if eaten: break
            for dy in range(-1, 2):
                if eaten: break
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < 10 and 0 <= ny < 10:
                    count = grid_counts[nx, ny]
                    for c in range(count):
                        f_idx = grid_indices[nx, ny, c]
                        if food_active[f_idx]: 
                            dist_sq = (food_x[f_idx] - tx)**2 + (food_y[f_idx] - ty)**2
                            if dist_sq < eat_dist_sq:
                                food_active[f_idx] = False
                                taro_energies[i] += 50.0
                                eaten = True
                                break

# --- 🧬 Numba：【命の循環】 ---
@njit
def find_empty_slot(alive_array):
    for i in range(len(alive_array)):
        if not alive_array[i]:
            return i
    return -1

@njit
def process_life_cycle(taro_x, taro_y, taro_alive, taro_energies, taro_speeds, taro_visions):
    for i in range(MAX_TARO):
        if not taro_alive[i]: continue

        taro_energies[i] -= 0.5 

        if taro_energies[i] <= 0:
            taro_alive[i] = False
            continue

        if taro_energies[i] >= 200.0:
            empty_idx = find_empty_slot(taro_alive)
            if empty_idx != -1: 
                taro_alive[empty_idx] = True
                taro_x[empty_idx] = taro_x[i]
                taro_y[empty_idx] = taro_y[i]
                
                taro_speeds[empty_idx] = max(0.5, taro_speeds[i] + (random.random() * 0.4 - 0.2))
                taro_visions[empty_idx] = max(2.0, taro_visions[i] + (random.random() * 2.0 - 1.0))
                
                taro_energies[i] -= 100.0
                taro_energies[empty_idx] = 100.0

# --- 🏃‍♂️ 移動システム ---
@njit
def update_movement_numba(x, y, alive, speeds, angles):
    for i in range(MAX_TARO):
        if alive[i]:
            x[i] = (x[i] + np.cos(angles[i]) * speeds[i]) % WORLD_SIZE
            y[i] = (y[i] + np.sin(angles[i]) * speeds[i]) % WORLD_SIZE

# --- 🎮 メインループ（ターミナル出力用） ---
def run_realtime_sim():
    print(f"🌍 16GB宇宙の創世：最大定員 太郎{MAX_TARO}匹 / 植物{MAX_FOOD}個")
    
    taro_x = np.zeros(MAX_TARO); taro_y = np.zeros(MAX_TARO)
    taro_speeds = np.zeros(MAX_TARO); taro_visions = np.zeros(MAX_TARO)
    taro_angles = np.zeros(MAX_TARO); taro_energies = np.zeros(MAX_TARO)
    taro_alive = np.zeros(MAX_TARO, dtype=np.bool_)

    food_x = np.zeros(MAX_FOOD); food_y = np.zeros(MAX_FOOD)
    food_active = np.zeros(MAX_FOOD, dtype=np.bool_)

    grid_counts = np.zeros((10, 10), dtype=np.int32)
    grid_indices = np.full((10, 10, 500), -1, dtype=np.int32)

    for i in range(1000):
        taro_x[i], taro_y[i] = random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE)
        taro_speeds[i] = random.uniform(1.0, 3.0)
        taro_visions[i] = random.uniform(5.0, 15.0)
        taro_energies[i] = 100.0
        taro_alive[i] = True

    spawn_food(food_x, food_y, food_active, 20000)

    print("🪄 Numbaエンジンをコンパイル中...")
    build_food_grid(food_x, food_y, food_active, grid_counts, grid_indices)
    update_ai_vision_grid(taro_x, taro_y, taro_alive, food_x, food_y, grid_counts, grid_indices, taro_visions, taro_angles)
    process_eating(taro_x, taro_y, taro_alive, taro_energies, food_x, food_y, food_active, grid_counts, grid_indices)
    process_life_cycle(taro_x, taro_y, taro_alive, taro_energies, taro_speeds, taro_visions)
    update_movement_numba(taro_x, taro_y, taro_alive, taro_speeds, taro_angles)
    print("✨ コンパイル完了！世界が動き出します！\n")

    for frame in range(1, 5001):
        start_time = time.time()
        
        spawn_food(food_x, food_y, food_active, 100)
        
        build_food_grid(food_x, food_y, food_active, grid_counts, grid_indices)
        update_ai_vision_grid(taro_x, taro_y, taro_alive, food_x, food_y, grid_counts, grid_indices, taro_visions, taro_angles)
        update_movement_numba(taro_x, taro_y, taro_alive, taro_speeds, taro_angles)
        process_eating(taro_x, taro_y, taro_alive, taro_energies, food_x, food_y, food_active, grid_counts, grid_indices)
        process_life_cycle(taro_x, taro_y, taro_alive, taro_energies, taro_speeds, taro_visions)

        calc_time = time.time() - start_time
        fps = 1.0 / calc_time if calc_time > 0 else 0
        
        if frame % 100 == 0:
            alive_count = np.sum(taro_alive)
            food_count = np.sum(food_active)
            avg_speed = np.mean(taro_speeds[taro_alive]) if alive_count > 0 else 0
            avg_vision = np.mean(taro_visions[taro_alive]) if alive_count > 0 else 0
            
            print(f"⏱️ 【Frame {frame}】 {calc_time:.4f}s ({fps:.0f} FPS) | 太郎: {alive_count}匹 | 植物: {food_count}個")
            print(f"    🧬 平均DNA -> Speed: {avg_speed:.2f} | Vision: {avg_vision:.2f}")

        if calc_time < 0.016:
            time.sleep(0.016 - calc_time)

if __name__ == "__main__":
    try:
        run_realtime_sim()
    except KeyboardInterrupt:
        print("\n🛑 神の意志により、世界の時間を停止しました。")
import math
import random

class Brain:
    def __init__(self):
        self.thisrdt_threshold = 0.6#どのくらい喉が渇いたら水を探し始めるのか。

    def think(self, ind, marsh):
        """
        個体の状態を見て次の動きを決定する
        """
        #1.欲求をチェック
        if ind.hydration < self.thisrdt_threshold:
            #2.目的地を特定
            #水域はy>500なので。今の自分がそれより上にいたら「下」を向く
            if ind.pos.y < marsh.water_y_line:
                return self._steer_towards_target(ind, ind.pos.x, marsh.water_y_line + 50)
            
        return ind.angle + random.uniform(-0.1, 0.1)
    
    def _steer_towards_target(self, ind, target_x, target_y):
        """
        目的地に向かって少しずつ角度を変える
        """
        dx = target_x - ind.pos.x
        dy = target_y - ind.pos.y
        desired_angle = math.atan2(dy ,dx)

        #今の角度を目的地に少し近づける
        diff = (desired_angle - ind.angle + math.pi)%(2*math.pi)-math.pi
        return ind.angle + max(-0.5, min (0.5,diff))
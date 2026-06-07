class Baseenvi:
    def __init__(self, 
                 name="基本環境",
                 water_depth = 0.0,
                 ground_softness = 0.2, 
                 gymnosperm_density = 0.5,
                 angiosperm_density =0.5,
                 prey_density = 0.5):
        
        self.name = name
        self. water_depth = water_depth
        self.ground_softness = ground_softness
        self.gymnosperm_density = gymnosperm_density
        self.angiosperm_density = angiosperm_density
        self.prey_density = prey_density

    def evaluate(self,target):

        raise NotImplemented("evaluateメソッドを子クラスで実装してください。")
class Robot:
    def __init__(self, context):
        self.context = context
        self.position_x = 0.0
        self.position_y = 0.0
        self.position_quality = 0.0
        self.current_zone = 0
        self.rotation = 0.0

        self.messages = []

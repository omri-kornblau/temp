class trajectory_point(object):
    """docstring for xpoint"""
    def __init__(self, x=0, y=0):
        self.left_time = 0
        self.right_time = 0
        self.time = 0
        self.y = x 
        self.x = y 
        self.angle = 0
        self.right_vel = 0 
        self.left_vel = 0
        self.right_acc = 0 
        self.left_acc = 0 
        self.right_jerk = 0 
        self.left_jerk = 0

    def update_distances (self, prev_point, angle_diff, width):
        dist = ((self.x-prev_point.x)**2 + (self.y-prev_point.y)**2)**0.5

        if (angle_diff > 0):
            rad = abs(dist/angle_diff)
            print ("radius", rad, type(rad))
            self.left_dist = dist*((rad-width/2)/rad)
            self.right_dist = dist*((rad+width/2)/rad)
        elif (angle_diff < 0):
            rad = abs(dist/angle_diff)
            print ("radius", rad, type(rad))
            self.left_dist = dist*((rad+width/2)/rad)
            self.right_dist = dist*((rad-width/2)/rad)
        else:
            self.left_dist = dist
            self.right_dist = dist

        print ("left_dist", self.left_dist)
        print ("right_dist", self.right_dist)

    def update_velocities_forward (self, prev_point, max_vel):        
        new_vel = (abs(2*prev_point.left_acc*self.left_dist + prev_point.left_vel**2))**0.5
        self.left_vel = min(max_vel, new_vel, key=abs)

        new_vel = (abs(2*prev_point.right_acc*self.right_dist + prev_point.right_vel**2))**0.5
        self.right_vel = min(max_vel, new_vel, key=abs)
        
        print ("prev_point.left_vel", prev_point.left_vel, type(prev_point.left_vel))
        print ("prev_point.left_acc", prev_point.left_acc, type(prev_point.left_acc))
        print ("prev_point.right_vel", prev_point.right_vel, type(prev_point.right_vel))
        print ("prev_point.right_acc", prev_point.right_acc, type(prev_point.right_acc))
        print ("left_vel", self.left_vel)
        print ("right_vel", self.right_vel)

    def update_velocities_backward (self, prev_point, max_vel):        
        print ("prev_point.left_vel", prev_point.left_vel, type(prev_point.left_vel))
        print ("prev_point.left_acc", prev_point.left_acc, type(prev_point.left_acc))
        
        new_vel = (abs(2*prev_point.left_acc*self.left_dist + prev_point.left_vel**2))**0.5
        self.left_vel = min(max_vel, self.left_vel, new_vel, key=abs)
        
        new_vel = (abs(2*prev_point.right_acc*self.right_dist + prev_point.right_vel**2))**0.5
        self.right_vel = min(max_vel, self.right_vel, new_vel, key=abs)

    def update_times_forward (self, prev_point):
        if abs(prev_point.left_acc) > 0:
            dt_left = (-1*prev_point.left_vel+(prev_point.left_vel**2 + abs(2*prev_point.left_acc*self.left_dist))**0.5)/prev_point.left_acc
        else:
            dt_left = self.left_dist/prev_point.left_vel

        self.left_time = prev_point.left_time + dt_left
        
        if abs(prev_point.right_acc) > 0:
            dt_right = (-1*prev_point.right_vel+(prev_point.right_vel**2 + abs(2*prev_point.right_acc*self.right_dist))**0.5)/prev_point.right_acc
        else:
            dt_right = self.right_dist/prev_point.right_vel

        self.right_time = prev_point.right_time + dt_right

        return dt_left, dt_right
    
    def update_times_backward (self, prev_point):
        if abs(prev_point.left_acc) > 0:
            dt_left = (-1*prev_point.left_vel+(prev_point.left_vel**2 + abs(2*prev_point.left_acc*self.left_dist))**0.5)/prev_point.left_acc
        else:
            dt_left = self.left_dist/prev_point.left_vel

        self.left_time = prev_point.left_time - dt_left
        
        if abs(prev_point.right_acc) > 0:
            dt_right = (-1*prev_point.right_vel+(prev_point.right_vel**2 + abs(2*prev_point.right_acc*self.right_dist))**0.5)/prev_point.right_acc
        else:
            dt_right = self.right_dist/prev_point.right_vel

        self.right_time = prev_point.right_time - dt_right

        return dt_left, dt_right
    
    def update_point(self, prev_point, dt_left, dt_right, faster_side, max_acc, max_vel):

        if faster_side == "right":
            self.left_vel  = self.left_dist/dt_right #self.right_vel*time_ratio*abs(self.right_dist/self.left_dist)
            self.right_acc = max(max_acc-max_acc*(self.right_vel/max_vel), 0.1)
            self.left_acc  = max(max_acc-max_acc*(self.left_vel/max_vel), 0.1)#self.right_acc*time_ratio*(self.right_vel-prev_point.right_vel)/(self.left_vel-prev_point.left_vel)
            self.left_time = self.right_time

        elif faster_side == "left":
            self.right_vel  = self.right_dist/dt_left #self.left_vel*time_ratio*abs(self.left_dist/self.right_dist)
            self.left_acc   = max(max_acc-max_acc*(self.left_vel/max_vel), 0.1)
            self.right_acc  = max(max_acc-max_acc*(self.right_vel/max_vel), 0.1) #self.left_acc*time_ratio*(self.left_vel-prev_point.left_vel)/(self.right_vel-prev_point.right_vel)
            self.right_time = self.left_time

        self.time = self.right_time
        
        print ("time:", self.time)

    def reset (self, max_acc):
        self.left_vel = 0
        self.right_vel = 0
        self.right_acc = max_acc
        self.left_acc = max_acc

    def sign (num):
        return((1, -1)[num < 0])

    # def update_vel_by_acc(self, prev_point):
    #     dist = ((self.x-prev_point.x)**2+(self.y-prev_point.y)**2)**0.5
    #     self.vel = (2*prev_point.acc*dist + prev_point.vel**2)**0.5

    # def update_vel_by_curve (self, prev_point):
    #     self.vel = self.vel*(self.radius+1)/self.radius
from __future__ import division

import math

def sign (num):
    return((1, -1)[num < 0])

def delta_angle (angle1, angle2):
    delta = angle1 - angle2
    if  delta > math.pi:
        delta -= 2 * math.pi
    elif delta < -math.pi:
        delta += 2 * math.pi
    return delta

class trajectory_point(object):
    """docstring for xpoint"""
    def __init__(self, x=0, y=0):
        self.time = 0
        self.y = y 
        self.x = x 
        self.angle = 0
        self.right_vel = 0 
        self.left_vel = 0
        self.right_acc = 0 
        self.left_acc = 0

        self.jerk = 10
        self.rule = 0

    def update_distances (self, prev_point, angle0 ,angle1, width):
        dist = math.sqrt((self.x-prev_point.x)**2 + (self.y-prev_point.y)**2)
        self.angle = angle1

        angle_diff = delta_angle(self.angle, angle0)

        if (abs(angle_diff) == 0):
            self.left_dist = dist
            self.right_dist = dist
        else:
            rad = dist/angle_diff
            self.left_dist = dist*((rad-width/2)/rad)
            self.right_dist = dist*((rad+width/2)/rad)

    def update_velocities_forward (self, prev_point, max_vel):        
        new_vel = (abs(2*prev_point.left_acc*self.left_dist + prev_point.left_vel**2))**0.5
        self.left_vel = min(max_vel, new_vel, key=abs)

        new_vel = (abs(2*prev_point.right_acc*self.right_dist + prev_point.right_vel**2))**0.5
        self.right_vel = min(max_vel, new_vel, key=abs)
        
        # print("left dist:", self.left_dist)
        # print ("right dist:", self.right_dist)
        # print ("left vel:",self.left_vel)
        # print ("prev left vel:", prev_point.left_vel)
        # print ("right_vel:", self.right_vel)
        # print ("prev right vel:", prev_point.right_vel)
        # print ("prev left acc:", prev_point.left_acc)
        # print ("prev right acc:", prev_point.right_acc)
        
    def update_velocities_backward (self, prev_point):                

        new_vel = (abs(2*prev_point.left_acc*prev_point.left_dist + prev_point.left_vel**2))**0.5
        self.left_vel = min(self.left_vel, new_vel, key=abs)
        
        new_vel = (abs(2*prev_point.right_acc*prev_point.right_dist + prev_point.right_vel**2))**0.5
        self.right_vel = min(self.right_vel, new_vel, key=abs)

        # print("left dist:", prev_point.left_dist)
        # print ("right dist:", prev_point.right_dist)
        # print ("left vel:",self.left_vel)
        # print ("prev left vel:", prev_point.left_vel)
        # print ("right_vel:", self.right_vel)
        # print ("prev right vel:", prev_point.right_vel)
        # print ("prev left acc:", prev_point.left_acc)
        # print ("prev right acc:", prev_point.right_acc)
    
    def update_times_forward (self, prev_point):
        dt_left = self.left_dist/(self.left_vel + 10**(-8))
        dt_right = self.right_dist/(self.right_vel + 10**(-8))

        return dt_left, dt_right
    
    def update_times_backward (self, prev_point):
        dt_left = prev_point.left_dist/(self.left_vel + 10**(-8))
        dt_right = prev_point.right_dist/(self.right_vel + 10**(-8))

        return dt_left, dt_right
    
    def update_point(self, prev_point, dt_left, dt_right, faster_side, max_acc, max_vel):
        if faster_side == "right":
            self.left_vel = self.left_dist/dt_right
            self.right_acc = max_acc #max(max_acc-max_acc*(abs(self.right_vel)/max_vel), 0.1)
            self.left_acc  = max_acc #(abs(self.left_vel-prev_point.left_vel))/dt_right 
            self.time = prev_point.time+dt_right
            self.rule = 1
    
        elif faster_side == "left":
            self.right_vel = self.right_dist/dt_left
            self.right_acc  = max_acc #(self.right_vel-prev_point.right_vel)/dt_left #self.left_acc*time_ratio*(self.left_vel-prev_point.left_vel)/(self.right_vel-prev_point.right_vel)
            self.left_acc   = max_acc #max(max_acc-max_acc*(abs(self.left_vel)/max_vel), 0.1)
            self.time = prev_point.time+dt_left
    
    def update_point_backward(self, prev_point, dt_left, dt_right, faster_side, max_acc, max_vel):
        if faster_side == "right":
            self.left_vel = prev_point.left_dist/dt_right
            self.right_acc = max_acc #max(max_acc-max_acc*(abs(self.right_vel)/max_vel), 0.1)
            self.left_acc  = max_acc #(self.left_vel-prev_point.left_vel)/dt_right
            self.time = prev_point.time-dt_right

        elif faster_side == "left":
            self.right_vel = prev_point.right_dist/dt_left
            self.right_acc  = max_acc #(self.right_vel-prev_point.right_vel)/dt_left #self.left_acc*time_ratio*(self.left_vel-prev_point.left_vel)/(self.right_vel-prev_point.right_vel)
            self.left_acc   = max_acc #max(max_acc-max_acc*(abs(self.left_vel)/max_vel), 0.1)
            self.time = prev_point.time-dt_left

    def reset (self, max_acc):
        self.left_vel = 0
        self.right_vel = 0
        self.right_acc = max_acc
        self.left_acc = max_acc




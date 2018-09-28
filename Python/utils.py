from __future__ import division

import math

def merge_dicts (dol1, dol2):
    keys = set(dol1).union(dol2)
    no = []
    return dict((k, dol1.get(k, no) + dol2.get(k, no)) for k in keys)

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
    def __init__(self, x=0, y=0, angle=0):
        self.time = 0
        self.y = y 
        self.x = x 
        self.angle = angle
        
        self.right_vel = 0 
        self.left_vel = 0
        
        self.right_acc = 0
        self.left_acc = 0

        self.dist = 0
        self.left_dist  = 0
        self.right_dist = 0

        self.rule = 0

    def update_distances (self, prev_point, angle0 ,angle1, width):
        self.dist = ((self.x-prev_point.x)**2 + (self.y-prev_point.y)**2)**0.5
        self.angle = angle1

        angle_diff = delta_angle(self.angle, angle0)

        if (abs(angle_diff) < 10**(-10)):
            self.left_dist = self.dist
            self.right_dist = self.dist
        else:
            rad = self.dist/angle_diff
            self.left_dist = self.dist*((rad-width/2)/rad)
            self.right_dist = self.dist*((rad+width/2)/rad)

    def update_velocities_forward (self, prev_point, max_vel):        
        new_vel = sign(self.left_dist)*((2*prev_point.left_acc*abs(self.left_dist) + prev_point.left_vel**2))**0.5
        self.left_vel = min(max_vel, new_vel, key=abs)

        new_vel = sign(self.right_dist)*((2*prev_point.right_acc*abs(self.right_dist) + prev_point.right_vel**2))**0.5
        self.right_vel = min(max_vel, new_vel, key=abs)

    def update_point_backward (self, prev_point, max_vel, max_acc, jerk):
        dt = prev_point.time - self.time
        
        right_acc = (self.right_vel-prev_point.right_vel)/dt 
        left_acc  = (self.left_vel-prev_point.left_vel)/dt
        
        if ((right_acc > max_acc) or (left_acc > max_acc)):
            if (right_acc > left_acc):
                self.right_vel =  sign(prev_point.right_dist)*((2*prev_point.right_acc*abs(prev_point.right_dist) + prev_point.right_vel**2))**0.5
                dt = prev_point.right_dist/self.right_vel
                self.left_vel = prev_point.left_dist/dt

                #master acc 
                self.right_acc  = min(prev_point.right_acc + jerk*dt, max_acc, key=abs)
                #slave acc
                cur_acc = (abs(self.left_vel-prev_point.left_vel))/dt
                self.left_acc  = min (cur_acc + jerk*dt, max_acc, key=abs) 

            else:
                self.left_vel =  sign(prev_point.left_dist)*((2*prev_point.left_acc*abs(prev_point.left_dist) + prev_point.left_vel**2))**0.5
                dt = prev_point.left_dist/self.left_vel
                self.right_vel = prev_point.right_dist/dt
                
                #master acc
                self.left_acc  = min(prev_point.left_acc + jerk*dt, max_acc, key=abs)
                #slave acc
                cur_acc = (abs(self.right_vel-prev_point.right_vel))/dt 
                self.right_acc  = min (cur_acc + jerk*dt, max_acc, key=abs) 
                
    def update_point(self, prev_point, max_vel, max_acc, jerk):
        dt_left  = self.left_dist/(self.left_vel + 10**(-8))
        dt_right = self.right_dist/(self.right_vel + 10**(-8))

        if dt_right > dt_left:
            #master
            self.left_vel  = self.left_dist/dt_right
            max_acc_by_vel = max(max_acc-max_acc*(abs(self.right_vel)/max_vel), 0.1)
            self.right_acc = min (prev_point.right_acc + jerk*dt_right, max_acc_by_vel, key=abs)
            
            #slave
            cur_acc = (abs(self.left_vel-prev_point.left_vel))/dt_right 
            max_acc_by_vel = max(max_acc-max_acc*(abs(self.left_vel)/max_vel), 0.1)
            self.left_acc  = min (cur_acc + jerk*dt_right, max_acc_by_vel, key=abs) 
            
            self.time = prev_point.time+dt_right
    
        else:
            #master
            self.right_vel  = self.right_dist/dt_left
            max_acc_by_vel = max(max_acc-max_acc*(abs(self.left_vel)/max_vel), 0.1)
            self.left_acc = min (prev_point.left_acc + jerk*dt_left, max_acc_by_vel, key=abs)
            
            #slave
            cur_acc = (abs(self.right_vel-prev_point.right_vel))/dt_left 
            max_acc_by_vel = max(max_acc-max_acc*(abs(self.right_vel)/max_vel), 0.1)
            self.right_acc  = min (cur_acc + jerk*dt_left, max_acc_by_vel, key=abs) 
            
            self.time = prev_point.time+dt_left
    
        self.left_vel_f  = self.left_vel
        self.right_vel_f = self.right_vel

    def reset (self, max_acc):
        self.left_vel  = 0
        self.right_vel = 0
        self.right_acc = 0.1
        self.left_acc  = 0.1

    def update_times (self, prev_point):
        self.time = prev_point.time + 2*self.dist/(prev_point.left_vel+prev_point.right_vel)


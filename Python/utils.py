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
    while  delta > math.pi:
        delta -= 2*math.pi
    while delta < -math.pi:
        delta += 2*math.pi

    return delta

class Robot (object):
    """defines robot's specs"""
    def __init__(self, params):
        self.max_vel = params.get("max_vel")
        self.slow_max_vel = params.get("slow_max_vel")
        self.max_acc = params.get("max_acc")
        self.max_angular_acc = params.get("max_angular_acc")
        self.jerk = params.get("jerk")
        self.width = params.get("width")
        self.height = params.get("height")
        self.cycle = params.get("cycle")

class point(object):
    """point in the path defined by the user"""
    def __init__(self, x, y, angle, heading, s_mag, e_mag, p_vel):
        self.x = x
        self.y = y
        self.angle = angle
        self.heading = heading
        self.start_mag = s_mag
        self.end_mag = e_mag
        self.p_vel = p_vel
        self.magnitude_factor = 1.2

        self.dx = math.cos(angle)*self.start_mag
        self.dy = math.sin(angle)*self.end_mag
        self.ddx = 0
        self.ddy = 0

    def distance (self, point):
        return math.sqrt((self.x-point.x)**2 + (self.y-point.y)**2)

    def update_v (self, point, is_start):
        # self.magnitude = self.magnitude_factor*self.distance(point)*0.5
        if is_start:
            mag = self.start_mag
        else:
            mag = self.end_mag

        self.dx = math.cos(self.angle)*mag
        self.dy = math.sin(self.angle)*mag

        pass

class trajectory_point(object):
    """single point in the path containes all
     the trajectory data of the point"""
    def __init__(self, x=0, y=0, angle=0, heading=0):
        self.time = 0
        self.y = y
        self.x = x
        self.angle = angle
        self.heading = heading
        self.wheading = 0
        self.vel = 0
        self.vx = 0
        self.vy = 0
        self.acc = 0
        self.dist = 0
        self.rule = 0
        self.slow_no_cam = False
        self.slow = False

    def update_distances (self, prev_point, angle):
        self.dist = ((self.x-prev_point.x)**2 + (self.y-prev_point.y)**2)**0.5
        self.angle = angle

    def update_point_backward (self, prev_point, max_vel, max_acc, jerk):
        dt = prev_point.time - self.time
        new_acc = (self.vel-prev_point.vel)/dt
        if (new_acc > max_acc):
            self.vel = sign(prev_point.dist)*((2*prev_point.acc*abs(prev_point.dist) + prev_point.vel**2))**0.5
            self.vel = min(max_vel, self.vel, key=abs)
            new_dt = prev_point.dist/self.vel
            self.acc = min(prev_point.acc + jerk*new_dt, max_acc, key=abs)


    def update_point_forward(self, prev_point, max_vel, max_acc, jerk):
        self.vel = sign(self.dist)*((2*prev_point.acc*abs(self.dist) + prev_point.vel**2))**0.5
        self.vel = min(max_vel, self.vel, key=abs)
        dt = self.dist/(self.vel + 10**(-8))

        max_acc_by_vel = max(max_acc-max_acc*(abs(self.vel)/max_vel), 0.1)
        self.acc = min(prev_point.acc + jerk*dt, max_acc_by_vel, key=abs)

        self.time = prev_point.time+dt

    def reset (self, max_acc):
        self.vel = 0
        self.acc = 0.1

    def update_point (self, prev_point):
        if ((prev_point.vel) == 0):
            dt = 0
        else:
            dt = self.dist/abs(prev_point.vel)

        self.time = prev_point.time + dt

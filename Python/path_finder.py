import numpy as np
import math
import json
import sys

from matplotlib import pyplot as plt
from scipy import optimize as opt
from velocity_finder import trajectory_point

class point(object):
    """docstring for dot"""
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        
        self.magnitude = 1
        self.magnitude_factor = 1.2
        self.dx = math.cos(angle)*self.magnitude
        self.dy = math.sin(angle)*self.magnitude
        self.ddx = 0
        self.ddy = 0

    def distance (self, point):
        return math.sqrt((self.x-point.x)**2 + (self.y-point.y)**2)

    def update_v (self, point):
        self.magnitude = self.magnitude_factor*self.distance(point)
        self.dx = math.cos(self.angle)*self.magnitude
        self.dy = math.sin(self.angle)*self.magnitude

class path_finder(object):
    """docstring for path_finder"""
    POS_COST    = 60000 #60000
    ANGLE_COST  = 6000  #6000
    RADIUS_COST = 50 #50 
    RADIUS_CONT_COST = 10
    LENGTH_COST = 0

    HIGHEST_POLYNOM = 5
    MIN = 0.
    MAX = 1.
    RES = 0.1
    OPTIMIZE_FUNCTION = 'BFGS'
    POWERS = []
            #'Nelder-Mead' 'Powell' 'CG' 'BFGS' 'Newton-CG' 'L-BFGS-B' 'TNC' 'COBYLA' 'SLSQP' 'trust-constr' 'dogleg' 'trust-ncg' 'trust-exact' 'trust-krylov'
    length_cost_val = 0
    
    RADIUS_SEG = 1
    RADIUS_COST_POWER = 1
    
    #                        meters^2                 radians^2                       
    COST_TOLS = {"pos_cost": (10**(-2)) **2 , "angle_cost": (1*math.pi/180) **2, "radius_cost": 1, "radius_cont_cost": 100} 

    #trajectory
    TIME_QUANT  = 3.0 #ms
    DEFAULT_SEG = 0.0000001
    END_S_THRES = 0.95

    def __init__(self, params, scalars_x, scalars_y, *args):
        """
        each parameter shold be a tuple of (x, y, angle)
        """
        self.costs = {}
        self.points = args
        self.path_amount = len(self.points)-1
        self.quintic = params.get("method")
        
        self.update_scalars(scalars_x, scalars_y, len(args), params.get("poly", 3))
        self.update_poly(params.get("poly", 3))
        self.update_costs_weights(params);

    def create_linear_scalar(self, param):
        scalars = np.zeros(len(self.points[:-1]) * (self.HIGHEST_POLYNOM + 1)).\
                     reshape(len(self.points[:-1]), (self.HIGHEST_POLYNOM + 1))

        for index in range(len(self.points[:-1])):
            param1 = self.points[index].__getattribute__(param)
            param2 = self.points[index + 1].__getattribute__(param)
            m = (param2 - param1) / (self.MAX - self.MIN)
            b = param1 - self.MIN * m 
            scalars[index][1] = m
            scalars[index][0] = b
        return scalars

    def create_quintic_scalar_x(self):
        scalars = np.zeros(len(self.points[:-1]) * (self.HIGHEST_POLYNOM + 1)).\
                     reshape(len(self.points[:-1]), (self.HIGHEST_POLYNOM + 1))

        for index in range(len(self.points[:-1])):
            self.points[index].update_v(self.points[index+1])
            self.points[index+1].update_v(self.points[index])
            p0 = self.points[index] 
            p1 = self.points[index+1]

            scalars[index][0] = p0.x
            scalars[index][1] = p0.dx
            scalars[index][2] = 0.5*p0.ddx
            scalars[index][3] = -10*p0.x-6*p0.dx-1.5*p0.ddx+0.5*p1.ddx-4*p1.dx+10*p1.x
            scalars[index][4] = 15*p0.x+8*p0.dx+1.5*p0.ddx-p1.ddx+7*p1.dx-15*p1.x
            scalars[index][5] = -6*p0.x-3*p0.dx-0.5*p0.ddx+0.5*p1.ddx-3*p1.dx+6*p1.x;

        return scalars

    def create_quintic_scalar_y(self):
        scalars = np.zeros(len(self.points[:-1]) * (self.HIGHEST_POLYNOM + 1)).\
                     reshape(len(self.points[:-1]), (self.HIGHEST_POLYNOM + 1))

        for index in range(len(self.points[:-1])):
            self.points[index].update_v(self.points[index+1])
            self.points[index+1].update_v(self.points[index])
            p0 = self.points[index] 
            p1 = self.points[index+1]

            scalars[index][0] = p0.y
            scalars[index][1] = p0.dy 
            scalars[index][2] = 0.5*p0.ddy
            scalars[index][3] = -10*p0.y-6*p0.dy-1.5*p0.ddy+0.5*p1.ddy-4*p1.dy+10*p1.y
            scalars[index][4] = 15*p0.y+8*p0.dy+1.5*p0.ddy-p1.ddy+7*p1.dy-15*p1.y
            scalars[index][5] = -6*p0.y-3*p0.dy-0.5*p0.ddy+0.5*p1.ddy-3*p1.dy+6*p1.y;

        return scalars

    def update_scalars(self, scalars_x, scalars_y, points_amount, wanted_poly):
        if (not scalars_x[0] == None):
            self.HIGHEST_POLYNOM = int(len(scalars_x)/(points_amount-1))-1
            self.scalars_x = np.array(scalars_x).reshape(points_amount-1, self.HIGHEST_POLYNOM+1)
            self.scalars_y = np.array(scalars_y).reshape(points_amount-1, self.HIGHEST_POLYNOM+1)
        
        elif (wanted_poly == 5) and (self.quintic):
            self.scalars_x = self.create_quintic_scalar_x()
            self.scalars_y = self.create_quintic_scalar_y()

        else:
            self.scalars_x = self.create_linear_scalar("x")
            self.scalars_y = self.create_linear_scalar("y")    
    
    def update_poly(self, val):
        poly_diff = val - self.HIGHEST_POLYNOM

        if (poly_diff > 0):
            zeros = np.zeros(len(self.points[:-1]) * (poly_diff)).reshape(len(self.points[:-1]) , poly_diff) 
            self.scalars_x = np.append(self.scalars_x, zeros , 1)
            self.scalars_y = np.append(self.scalars_y, zeros , 1)
        elif (poly_diff < 0):
            self.scalars_x = np.delete(self.scalars_x, np.s_[(abs(poly_diff-2)):], 1)
            self.scalars_y = np.delete(self.scalars_y, np.s_[(abs(poly_diff-2)):], 1)

        self.HIGHEST_POLYNOM = val
        self.POWERS = np.arange(self.HIGHEST_POLYNOM+1)

    def update_costs_weights (self, params):
        self.POS_COST         = params.get("pos", 1)*6000000000
        self.ANGLE_COST       = params.get("angle", 1)*6000000000
        self.RADIUS_COST      = params.get("radius", 1)*100
        self.RADIUS_CONT_COST = params.get("radius_cont", 1)*100
        self.LENGTH_COST      = params.get("length", 0)*0.00001

    def x(self, index, s):
        """
        :param int index: the index of the path
        :param float s: the index of s betwin MIN to MAX
        """
        answer = np.matmul(np.power(s, self.POWERS),(self.scalars_x[index]))
        return answer

    def y(self, index, s):
        """
        :param int index: the index of the path
        :param float s: the index of s betwin MIN to MAX
        """
        answer = np.matmul(np.power(s, self.POWERS),(self.scalars_y[index]))
        return answer

    def dxds(self, index, s):
        answer = np.matmul(np.power(s, self.POWERS[:-1]), (self.scalars_x[index][1:]*self.POWERS[1:]))
        return answer

    def dyds(self, index, s):
        answer = np.matmul(np.power(s, self.POWERS[:-1]), (self.scalars_y[index][1:]*self.POWERS[1:]))
        return answer

    def d2xds2(self, index, s):
        """
        second derivative x
        """
        answer = 0.
        for i in range(len(self.scalars_x[index]) - 1, 1, -1):
            answer = answer * s + (self.scalars_x[index][i] * i * (i - 1))  
        return answer

    def d2yds2(self, index, s):
        """ 
        second derivative y
        """
        answer = 0.
        for i in range(len(self.scalars_y[index]) - 1, 1, -1):
            answer = answer * s + (self.scalars_y[index][i] * i * (i - 1))
        return answer
    
    def radius (self, index, s):
        dx = self.dxds(index, s)
        d2x = self.d2xds2(index, s)
        dy = self.dyds(index, s)
        d2y = self.d2yds2(index, s)
        if (((d2x * dy) - (d2y * dx)) == 0):
            return 10**20
        return ((dx ** 2) + (dy ** 2))**1.5 / ((d2x * dy) - (d2y * dx))
    
    def delta_angle(self, angle1, angle2):
        delta = angle1 - angle2
        if  delta > math.pi:
            delta -= 2 * math.pi
        elif delta < -math.pi:
            delta += 2 * math.pi
        return delta
    
    def get_position_costs(self):
        cost = 0.
        amount_of_points = self.path_amount
        for index in range(amount_of_points):
            cost += (self.x(index, self.MIN) - self.points[index].x) ** 2
            cost += (self.x(index, self.MAX) - self.points[index + 1].x) ** 2
            cost += (self.y(index, self.MIN) - self.points[index].y) ** 2
            cost += (self.y(index, self.MAX) - self.points[index + 1].y) ** 2
        return cost/((amount_of_points+1) * 4)

    def get_angle_costs(self):
        cost = 0.
        amount_of_points = self.path_amount
        for index in range(amount_of_points):
            start_angle = math.atan2(self.dyds(index, self.MIN), self.dxds(index, self.MIN))
            end_angle = math.atan2(self.dyds(index, self.MAX), self.dxds(index, self.MAX))
            cost += (self.delta_angle(start_angle, self.points[index].angle)) ** 2
            cost += (self.delta_angle(end_angle, self.points[index + 1].angle)) ** 2
        return cost / ((amount_of_points+1) * 2)
    
    def get_radius_cost(self):
        cost = 0
        counter = 0
        for index in range(self.path_amount):
            #for s in ( np.cbrt(((np.arange(self.MIN, self.MAX + self.RES,  self.RES))-0.5)*2)*0.5 + 0.5):
            for s in np.arange(self.MIN, self.MAX + self.RES,  self.RES):
                #cost += (1/self.radius(index ,s)) ** 4
                
                dx = self.dxds(index, s)
                d2x = self.d2xds2(index, s)
                dy = self.dyds(index, s)
                d2y = self.d2yds2(index, s)

                cost +=  (((d2x * dy) - (d2y * dx)) / ((dx ** 2) + (dy ** 2))**1.5)**4

                self.length_cost_val += math.sqrt((self.dxds(index, s)/self.RES)**2 + (self.dyds(index, s)/self.RES)**2)
                
                counter += 1
        cost /= counter
        return cost
    
    def get_length_cost (self):
        return self.length_cost_val

    def get_radius_cont_cost(self):
        cost = 0
        counter = 1

        if (self.path_amount-1 > 0):
            counter = 0

        for index in range(self.path_amount - 1):
            rad = self.radius(index, self.MAX)
            last_rad = self.radius(index+1, self.MIN)
            
            cost += (last_rad-rad) ** 2
            counter += 1
        return cost/counter

    def get_highest_power_cost(self):
        return (sum([scalar[self.HIGHEST_POLYNOM] ** 2 for scalar in self.scalars_x])\
               + sum([scalar[self.HIGHEST_POLYNOM] ** 2 for scalar in self.scalars_y]))

    def cost_function(self, args):
        args = np.array(args)
        
        self.scalars_x = args[:int(len(args) / 2) ]
        self.scalars_y = args[int(len(args) / 2 ):]
        self.scalars_x = np.array(self.scalars_x).reshape(len(self.points) - 1, self.HIGHEST_POLYNOM + 1)
        self.scalars_y = np.array(self.scalars_y).reshape(len(self.points) - 1, self.HIGHEST_POLYNOM + 1)
        
        self.costs["pos_cost"]         = self.get_position_costs()
        self.costs["angle_cost"]       = self.get_angle_costs()
        self.costs["radius_cost"]      = self.get_radius_cost()
        self.costs["radius_cont_cost"] = self.get_radius_cont_cost()
        self.costs["length_cost"]      = self.get_length_cost()

        costs_weighted = {}
        costs_weighted["pos_cost"]         = self.POS_COST * self.costs["pos_cost"]
        costs_weighted["angle_cost"]       = self.ANGLE_COST * self.costs["angle_cost"]
        costs_weighted["radius_cost"]      = self.RADIUS_COST * self.costs["radius_cost"]
        costs_weighted["radius_cont_cost"] = self.RADIUS_CONT_COST * self.costs["radius_cont_cost"]
        costs_weighted["length_cost"]      = self.LENGTH_COST * self.costs["length_cost"]

        return sum(costs_weighted.values())

    def quintic_cost_function(self, args):
        
        for index, point in enumerate(self.points):
            point.ddx = args[index*2]
            point.ddy = args[index*2+1]
            point.magnitude_factor = args[index*3+2]
        
        self.scalars_x = self.create_quintic_scalar_x()
        self.scalars_y = self.create_quintic_scalar_y()
        
        self.costs["pos_cost"]         = self.get_position_costs()
        self.costs["angle_cost"]       = self.get_angle_costs()
        self.costs["radius_cost"]      = self.get_radius_cost()
        self.costs["radius_cont_cost"] = self.get_radius_cont_cost()
        self.costs["length_cost"]      = self.get_length_cost()

        costs_weighted = {}
        #costs_weighted["pos_cost"]         = self.POS_COST * self.costs["pos_cost"]
        costs_weighted["angle_cost"]       = self.ANGLE_COST * self.costs["angle_cost"]
        costs_weighted["radius_cost"]      = self.RADIUS_COST * self.costs["radius_cost"]
        costs_weighted["radius_cont_cost"] = self.RADIUS_CONT_COST * self.costs["radius_cont_cost"]
        costs_weighted["length_cost"]      = self.LENGTH_COST * self.costs["length_cost"]

        return sum(costs_weighted.values())

    def get_costs(self):
        return self.costs

    def find_scalars(self):
        if (self.quintic):
            args = []
            for point in self.points:
                args.append(point.ddx)
                args.append(point.ddy)
                args.append(point.magnitude_factor)

            opt.minimize(self.quintic_cost_function, args, method = self.OPTIMIZE_FUNCTION)
        else:
            opt.minimize(self.cost_function, np.ravel([self.scalars_x, self.scalars_y]), method = self.OPTIMIZE_FUNCTION)

    def find_trajectory(self, max_vel, max_acc, width):
        xpoints = [trajectory_point(self.x(0, self.MIN), self.y(0, self.MIN))]

        xpoints[0].reset(max_acc)

        i = 0

        #run forward
        for path in range(self.path_amount):
            s = self.MIN
            ds_index = 1   
            start_ds = []

            while s <= self.MAX:
                #if (s < (self.END_S_THRES)):
                min_vel = abs(xpoints[i].left_vel+xpoints[i].right_vel)/2
                new_ds = (min_vel*(self.TIME_QUANT/1000)) / ((self.dxds(path, s) ** 2 + self.dyds(path, s) ** 2)**0.5)

                ds = max(new_ds, self.DEFAULT_SEG)
                    
                if ds > 0.01:
                    ds = 0.01

                    #if (s < (1-self.END_S_THRES)):
                    #    start_ds.append(ds)

                # else:
                #     ds = start_ds[-ds_index]
                #     ds_index += 1
                
                if (s+ds <= 1):
                    xpoints.append(trajectory_point(self.x(path, s+ds), self.y(path, s+ds)))
                elif (path + 1 < self.path_amount):
                    xpoints.append(trajectory_point(self.x(path+1, s+ds-1), self.y(path+1, s+ds-1)))
                else:
                    break

                angle_0 = math.atan2(self.dyds(path, s), self.dxds(path, s))
                angle_1 = math.atan2(self.dyds(path, s+ds), self.dxds(path, s+ds))

                xpoints[i+1].update_distances(xpoints[i],angle_0, angle_1, width)

                xpoints[i+1].update_velocities_forward(xpoints[i], max_vel)

                dt_left, dt_right = xpoints[i+1].update_times_forward(xpoints[i]) #xpoint[i-1].vel+xpoint[i-1].max_acc*
                
                if (dt_left < dt_right):
                    xpoints[i+1].update_point(xpoints[i], dt_left, dt_right, "right", max_acc, max_vel)
                else:
                    xpoints[i+1].update_point(xpoints[i], dt_left, dt_right, "left", max_acc, max_vel)

                i += 1
                s += ds

        sec_point_time = xpoints[0].time
        xpoints[-1].reset(max_acc)

        while (i > 0): 
            xpoints[i-1].update_velocities_backward(xpoints[i], max_vel)

            dt_left, dt_right = xpoints[i-1].update_times_backward(xpoints[i]) #xpoint[i-1].vel+xpoint[i-1].max_acc*
            
            if (dt_left < dt_right):
                xpoints[i-1].update_point_backward(xpoints[i], dt_left, dt_right, "right", max_acc, max_vel)
            else:
                xpoints[i-1].update_point_backward(xpoints[i], dt_left, dt_right, "left", max_acc, max_vel)
            
            i -= 1

        sec_point_time_after = xpoints[0].time
        dt = sec_point_time - sec_point_time_after
        
        for xpoint in xpoints:
            xpoint.time += dt

        return xpoints
    def draw_graph(self, res):
        xs = []
        ys = []
        for index in range(self.path_amount):
            for s in np.arange(self.MIN, self.MAX + res, res):
                xs.append(self.x(index, s))
        for index in range(self.path_amount):
            for s in np.arange(self.MIN, self.MAX + res, res):
                ys.append(self.y(index, s))
        return (xs,ys)
 
    def create_data(self):
        xs, ys = self.draw_graph(0.001)
        path_points = []
        for i in range(len(xs)):
            path_points.append({"x":xs[i], "y":ys[i]})
        data = {"path_points": path_points, "costs": self.costs, "scalars_x": list(np.ravel(self.scalars_x)), "scalars_y": list(np.ravel(self.scalars_y))}
        return data

def main(in_data):
    paths = []
    out_data = []

##########################################Testing#################################
    #in_data = [{"params":{"poly":5,"pos":1,"angle":1,"radius":1,"radius_cont":0.1,"length":0,"method":True},"points":[{"x":1,"y":1,"heading":0,"switch":"false"},{"x":5,"y":5,"heading":0,"switch":"false"}],"scalars_x":[None],"scalars_y":[None]}]
    #in_data = [{"params":{"poly":5,"pos":1,"angle":1,"radius":1,"radius_cont":0.1,"length":0,"method":True},"points":[{"x":1,"y":1,"heading":1.5707963267948966,"switch":"false"},{"x":3,"y":3,"heading":0,"switch":"false"}],"scalars_x":[None],"scalars_y":[None]}]
    #in_data = [{"params":{"poly":5,"pos":1,"angle":1,"radius":1,"radius_cont":0.1,"length":0,"method":True},"points":[{"x":0,"y":1,"heading":0,"switch":"false"},{"x":3,"y":1,"heading":0,"switch":"false"}],"scalars_x":[None],"scalars_y":[None]}]
    #in_data = [{"params":{"poly":5,"pos":1,"angle":1,"radius":1,"radius_cont":0.1,"length":0,"method":True},
    #   "points":[{"x":1,"y":1,"heading":0,"switch":"false"},
    #   {"x":5,"y":1,"heading":0,"switch":"false"},
    #   {"x":5,"y":5,"heading":1.1517,"switch":"false"}],"scalars_x":[None],"scalars_y":[None]}]
    #get data from GUI
##########################################Testing#################################
    
    in_data = json.loads(in_data)
    
    #set up path_finder objects
    for index, path_data in enumerate(in_data):
        path_points = [point(path_point["x"], path_point["y"], path_point["heading"]) for path_point in path_data["points"]]
        if (index>0):
            path_points[0].angle += math.pi
        paths.append(path_finder(
            path_data["params"], 
            path_data["scalars_x"],
            path_data["scalars_y"],
            *path_points))
        
    for path in paths:
        #the reason we are all here:
        path.find_scalars()
        out_data.append(path.create_data())

    #send the data to the GUI
##########################################Testing#################################    
    print (json.dumps(out_data))
    for path in paths:
        xpoints = path.find_trajectory(3.5, 8.0, 0.9)

    left_vel = []
    right_vel = []
    left_acc = []
    right_acc = []
    times = []
    dts = []

    for i in range(len(xpoints)):
        left_vel.append(xpoints[i].left_vel)
        right_vel.append(xpoints[i].right_vel)
        
        if (i < len(xpoints) -1):
            left_acc.append((xpoints[i+1].left_vel-xpoints[i].left_vel)/(xpoints[i+1].time-xpoints[i].time))
            right_acc.append((xpoints[i+1].right_vel-xpoints[i].right_vel)/(xpoints[i+1].time-xpoints[i].time))
            dts.append(xpoints[i+1].time-xpoints[i].time)
        
        times.append(xpoints[i].time)

    traj_p = plt.subplot (3, 1, 1)
    acc_p  = plt.subplot (3, 1, 2)
    path_p = plt.subplot (3, 1, 3)
    
    path_p.axis('equal')
    
    indicies = range(len(xpoints)-2) 

    acc_p .plot(times[:-1], right_acc)
    acc_p .plot(times[:-1], left_acc)
    #acc_p.plot(times[:-1], dts)
    acc_p.set(xlabel='points', ylabel='dts')
    acc_p.grid()

    traj_p.plot(times, right_vel)
    traj_p.plot(times, left_vel)
    traj_p.set(xlabel='time', ylabel='Velocity')
    traj_p.grid()

    path_p.plot(paths[0].draw_graph(0.01)[0], paths[0].draw_graph(0.01)[1])
    path_p.set(xlabel='X', ylabel='Y')
    path_p.grid()

    plt.show()
    plt.close('all')
if __name__ == "__main__":
    main(sys.argv[1])

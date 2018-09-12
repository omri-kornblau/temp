from scipy import optimize as opt
import numpy as np
import math
import json
import sys

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
            #'Nelder-Mead' 'Powell' 'CG' 'BFGS' 'Newton-CG' 'L-BFGS-B' 'TNC' 'COBYLA' 'SLSQP' 'trust-constr' 'dogleg' 'trust-ncg' 'trust-exact' 'trust-krylov'
    RADIUS_SEG = 1
    RADIUS_COST_POWER = 1
    #                        meters^2                 radians^2                       
    COST_TOLS = {"pos_cost": (10**(-2)) **2 , "angle_cost": (1*math.pi/180) **2, "radius_cost": 1, "radius_cont_cost": 100} 

    # miliseconds
    TIME_QUANT = 2
    length_cost_val = 0

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
        answer = 0.
        for i in range(len(self.scalars_x[index]) - 1, -1, -1):
            answer = answer * s + self.scalars_x[index][i]
        return answer

    def y(self, index, s):
        """
        :param int index: the index of the path
        :param float s: the index of s betwin MIN to MAX
        """
        answer = 0.
        for i in range(len(self.scalars_y[index]) - 1, -1, -1):
            answer = answer * s + self.scalars_y[index][i]
        return answer

    def dxds(self, index, s):
        answer = 0.
        for i in range(len(self.scalars_x[index]) - 1, 0, -1):
            answer = answer * s + (self.scalars_x[index][i] * i)
        return answer

    def dyds(self, index, s):
        answer = 0.
        for i in range(len(self.scalars_y[index]) - 1, 0, -1):
            answer = answer * s + (self.scalars_y[index][i] * i)
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
            for s in np.arange(self.MIN, self.MAX + self.RES,  self.RES * self.RADIUS_SEG):
                dx = self.dxds(index, s)
                d2x = self.d2xds2(index, s)
                dy = self.dyds(index, s)
                d2y = self.d2yds2(index, s)
                cost += (((d2x * dy) - (d2y * dx)) / (((dx ** 2) + (dy ** 2)) ** 1.5)) ** 4

                self.length_cost_val += math.sqrt((dx/self.RES)**2 + (dy/self.RES)**2)
                counter += 1
        cost /= counter
        return cost
    
    def get_length_cost (self):
        return self.length_cost_val

    def get_radius_cont_cost(self):
        cost = 0
        last_rad = 0
        counter = 1
        if (self.path_amount-1 > 0):
            counter = 0
        for index in range(self.path_amount - 1):
            dx = self.dxds(index, 1)
            d2x = self.d2xds2(index, 1)
            dy = self.dyds(index, 1)
            d2y = self.d2yds2(index, 1)
            rad = ((d2x * dy) - (d2y * dx)) / (((dx ** 2) + (dy ** 2)) ** 1.5)
            
            dx = self.dxds(index+1, -1)
            d2x = self.d2xds2(index+1, -1)
            dy = self.dyds(index+1, -1)
            d2y = self.d2yds2(index+1, -1)
            last_rad = ((d2x * dy) - (d2y * dx)) / (((dx ** 2) + (dy ** 2)) ** 1.5) 
            
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
        #return opt.minimize(self.cost_function, np.ravel([self.scalars_x, self.scalars_y]), method = self.OPTIMIZE_FUNCTION, cost_tol = self.COST_TOLS, get_costs = self.get_costs)
        if (self.quintic):
            args = []
            for point in self.points:
                args.append(point.ddx)
                args.append(point.ddy)
                args.append(point.magnitude_factor)
            opt.minimize(self.quintic_cost_function, args, method = self.OPTIMIZE_FUNCTION)
        
        else:
            opt.minimize(self.cost_function, np.ravel([self.scalars_x, self.scalars_y]), method = self.OPTIMIZE_FUNCTION)

    def find_velocities(self):
        xpoints = [xpoint(self.x(0, -1), self.y(0, -1))]
        xpoint_index = 0

        for path in range(self.path_amount):
            s = -1
            while s <= 1:
                ds = xpoints[xpoint_index].velocity * TIME_QUANT / Sqr(self.dxds(path, s) ^ 2 + self.dyds(path, s) ^ 2)


                xpoint_index += 1

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

    #get data from GUI
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
    print (json.dumps(out_data))

if __name__ == "__main__":
    main(sys.argv[1])

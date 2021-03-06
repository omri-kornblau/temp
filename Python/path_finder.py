from __future__ import division
from matplotlib import pyplot as plt
from scipy import optimize as opt
from utils import trajectory_point

import numpy as np
import random
import math
import json
import sys
import utils
import copy

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
    RES = 0.05
    OPTIMIZE_FUNCTION = 'BFGS' #Need to make solver test..
    QUINTIC_OPTIMIZE_FUNCTION = 'BFGS'
    #'Nelder-Mead' 'Powell' 'CG' 'BFGS' 'Newton-CG' 'L-BFGS-B' 'TNC' 'COBYLA' 'SLSQP' 'trust-constr' 'dogleg' 'trust-ncg' 'trust-exact' 'trust-krylov'
    POWERS = []
    length_cost_val = 0

    RADIUS_SEG = 1
    RADIUS_COST_POWER = 1

    #                        meters^2                 radians^2
    COST_TOLS = {"pos_cost": (10**(-2)) **2 , "angle_cost": (1*math.pi/180) **2, "radius_cost": 1, "radius_cont_cost": 100}

    #trajectory
    TIME_QUANT  = 1 #ms
    DEFAULT_DS = 1e-5
    END_S_THRES = 0.97

    DELAY_OMEGA = 0.140 #s

    def __init__(self, params, scalars_x, scalars_y, slow_start, slow_end, *points):
        """
        each parameter should be a tuple of (x, y, angle)
        """
        self.costs = {}
        self.points = points
        self.path_amount = len(self.points)-1
        self.quintic = params.get("method")

        self.slow_start = slow_start
        self.slow_end = slow_end

        self.update_scalars(scalars_x, scalars_y, len(points), params.get("poly", 3))
        self.update_poly(params.get("poly", 3))
        self.update_costs_weights(params)
        self.trajectory = []
        self.regulator = (np.random.rand(int((self.path_amount+1)*(1/self.RES) + 1)) - 0.5)*self.RES/100

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
            self.points[index].update_v(self.points[index+1], False)
            self.points[index+1].update_v(self.points[index], True)
            p0 = self.points[index]
            p1 = self.points[index+1]

            scalars[index][0] = p0.x
            scalars[index][1] = p0.dx
            scalars[index][2] = 0.5*p0.ddx
            scalars[index][3] = -10*p0.x-6*p0.dx-1.5*p0.ddx+0.5*p1.ddx-4*p1.dx+10*p1.x
            scalars[index][4] = 15*p0.x+8*p0.dx+1.5*p0.ddx-p1.ddx+7*p1.dx-15*p1.x
            scalars[index][5] = -6*p0.x-3*p0.dx-0.5*p0.ddx+0.5*p1.ddx-3*p1.dx+6*p1.x

        return scalars

    def create_quintic_scalar_y(self):
        scalars = np.zeros(len(self.points[:-1]) * (self.HIGHEST_POLYNOM + 1)).\
                     reshape(len(self.points[:-1]), (self.HIGHEST_POLYNOM + 1))

        for index in range(len(self.points[:-1])):
            self.points[index].update_v(self.points[index+1], False)
            self.points[index+1].update_v(self.points[index], True)
            p0 = self.points[index]
            p1 = self.points[index+1]

            scalars[index][0] = p0.y
            scalars[index][1] = p0.dy
            scalars[index][2] = 0.5*p0.ddy
            scalars[index][3] = -10*p0.y-6*p0.dy-1.5*p0.ddy+0.5*p1.ddy-4*p1.dy+10*p1.y
            scalars[index][4] = 15*p0.y+8*p0.dy+1.5*p0.ddy-p1.ddy+7*p1.dy-15*p1.y
            scalars[index][5] = -6*p0.y-3*p0.dy-0.5*p0.ddy+0.5*p1.ddy-3*p1.dy+6*p1.y

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
        self.POS_COST         = params.get("position", 1)*6000000000
        self.ANGLE_COST       = params.get("angle", 1)*6000000000
        self.RADIUS_COST      = params.get("radius", 1)*0.1
        self.RADIUS_CONT_COST = params.get("radius_cont", 1)*.001
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

        # if (((d2x * dy) - (d2y * dx)) == 0):
        #     return (float(10**5))

        return  ((d2x*dy) - (d2y*dx)) / ((dx**2) + (dy**2))**1.5

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
            cost += (utils.delta_angle(start_angle, self.points[index].angle)) ** 2
            cost += (utils.delta_angle(end_angle, self.points[index + 1].angle)) ** 2
        return cost / ((amount_of_points+1) * 2)

    def get_radius_cost(self):
        cost = 0
        counter = 0
        self.length_cost_val = 0

        for index in range(self.path_amount):
            # for s in ( np.cbrt(((np.arange(self.MIN, self.MAX + self.RES,  self.RES))-0.5)*2)*0.5 + 0.5):
            for s in np.arange(self.MIN, self.MAX + self.RES,  self.RES):
                # regulator = self.regulator[counter]

                dx = self.dxds(index, s)
                d2x = self.d2xds2(index, s)
                dy = self.dyds(index, s)
                d2y = self.d2yds2(index, s)

                cost +=  (((d2x*dy) - (d2y*dx))/((dx**2) + (dy**2))**1.5)**4

                self.length_cost_val += math.sqrt((self.x(index, s) - self.x(index, s-self.RES))**2 + (self.y(index, s) - self.y(index, s-self.RES))**2)
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

        if (self.path_amount > 1):
            for index in range(self.path_amount - 1):
                curv = self.radius(index, self.MAX)
                last_curv = self.radius(index+1, self.MIN)
                # curv = math.sqrt(self.d2xds2(index, self.MAX)**2+self.d2yds2(index, self.MAX)**2)
                # last_curv = math.sqrt(self.d2xds2(index+1, self.MIN)**2+self.d2yds2(index+1, self.MIN)**2)

                cost += (last_curv-curv) ** 2
                counter += 1
        else:
            cost = 0

        return cost/counter

    def get_highest_power_cost(self):
        return (sum([scalar[self.HIGHEST_POLYNOM] ** 2 for scalar in self.scalars_x])\
               + sum([scalar[self.HIGHEST_POLYNOM] ** 2 for scalar in self.scalars_y]))

    def get_mag_size_cost (self):
        cost = 0
        for point in self.points:
            mag = point.start_mag
            #cost += ((point.magnitude_factor-1.2))**6 #(0.1**2)*((point.magnitude_factor-1.2))**2
            cost += 415+(-843)*mag+602*(mag**2)+(-177)*(mag**3)+18.5*(mag**4)
        return cost

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
            # point.magnitude = args[index*3+2]

        self.scalars_x = self.create_quintic_scalar_x()
        self.scalars_y = self.create_quintic_scalar_y()

        self.costs["pos_cost"]         = self.get_position_costs()
        self.costs["angle_cost"]       = self.get_angle_costs()
        self.costs["radius_cost"]      = self.get_radius_cost()
        self.costs["radius_cont_cost"] = self.get_radius_cont_cost()
        self.costs["length_cost"]      = self.get_length_cost()
        # self.costs["mag_size_cost"]    = self.get_mag_size_cost()

        costs_weighted = {}
#        costs_weighted["pos_cost"]         = self.POS_COST * self.costs["pos_cost"]
        costs_weighted["angle_cost"]       = self.ANGLE_COST * self.costs["angle_cost"]
        costs_weighted["radius_cost"]      = self.RADIUS_COST * self.costs["radius_cost"]
        costs_weighted["radius_cont_cost"] = self.RADIUS_CONT_COST * self.costs["radius_cont_cost"]
        costs_weighted["length_cost"]      = self.LENGTH_COST * self.costs["length_cost"]
        # costs_weighted["mag_size_cost"]    = 0*self.costs["mag_size_cost"]

        return sum(costs_weighted.values())

    def get_costs(self):
        return self.costs

    def find_scalars(self):
        if (self.quintic):
            args = []
            for point in self.points:
                args.append(point.ddx)
                args.append(point.ddy)
                # args.append(point.magnitude)

            opt.minimize(self.quintic_cost_function, args, method = self.QUINTIC_OPTIMIZE_FUNCTION, options={"eps":1.5e-04})
        else:
            opt.minimize(self.cost_function, np.ravel([self.scalars_x, self.scalars_y]), method = self.OPTIMIZE_FUNCTION)

    def find_basic_trajectory(self, robot, time_offset):
        first_point_angle = math.atan2(self.dyds(0, self.MIN), self.dxds(0, self.MIN))

        total_dist = 0

        tpoints = [trajectory_point(self.x(0, self.MIN), self.y(0, self.MIN), first_point_angle)]
        tpoints[0].reset(robot.max_acc)

        i = 0
        s = self.MAX

        points_timestamps = [tpoints[0]]

        #run forward
        for path in range(self.path_amount):
            s -= self.MAX

            ds_index = 0
            end_ds = []

            while s < self.MAX:
                #choose 's' increment called ds according to the velocity
                if (s*(path+1.0) < (self.END_S_THRES+(self.path_amount-1.0)*self.MAX)):
                    min_vel = tpoints[i].vel
                    new_ds = (min_vel*(self.TIME_QUANT/1000.0)) / ((self.dxds(path, s) ** 2 + self.dyds(path, s) ** 2)**0.5)

                    ds = max(new_ds, self.DEFAULT_DS)

                    #Protection from too high ds
                    if ds > 0.001:
                        ds = 0.001

                    #Store all the ds's of the begininng to use in the end
                    #of the path when the velocity is higher
                    if (s < (self.MAX-self.END_S_THRES)):
                        end_ds.append(ds)
                        ds_index += 1

                elif ds_index < 0:
                    ds = end_ds[ds_index]
                    ds_index -= 1
                else:
                    ds = self.DEFAULT_DS

                start_angle = math.atan2(self.dyds(path, s), self.dxds(path, s))

                if (s+ds <= self.MAX):
                    robot.max_vel = self.points[path + 1].p_vel
                    tpoints.append(trajectory_point(self.x(path, s+ds), self.y(path, s+ds)))
                    end_angle = math.atan2(self.dyds(path, s+ds), self.dxds(path, s+ds))
                elif (path + 1 < self.path_amount):
                    points_timestamps.append(tpoints[i])
                    robot.max_vel = self.points[path + 1].p_vel
                    tpoints.append(trajectory_point(self.x(path+1, s+ds-self.MAX), self.y(path+1, s+ds-self.MAX)))
                    end_angle = math.atan2(self.dyds(path+1, s+ds-self.MAX), self.dxds(path+1, s+ds-self.MAX))
                else:
                    points_timestamps.append(tpoints[i])
                    break

                tpoints[i+1].update_distances(tpoints[i], end_angle)

                total_dist += tpoints[i+1].dist

                if (total_dist < self.slow_start):
                    tpoints[i+1].update_point_forward(tpoints[i], robot.slow_max_vel, robot.max_acc, robot.jerk)
                    tpoints[i+1].slow_no_cam = True
                elif (total_dist < (self.length_cost_val-self.slow_end)):
                    tpoints[i+1].update_point_forward(tpoints[i], robot.max_vel, robot.max_acc, robot.jerk)
                    tpoints[i+1].slow = False
                else:
                    tpoints[i+1].update_point_forward(tpoints[i], robot.slow_max_vel, robot.max_acc, robot.jerk)
                    tpoints[i+1].slow = True
                    tpoints[i+1].slow_no_cam = True

                i += 1
                s += ds

        tpoints[-1].reset(robot.max_acc)
        #run backward
        while (i > 1):
            tpoints[i-1].update_point_backward(tpoints[i], robot.max_vel, robot.max_acc, robot.jerk)
            i -= 1

        tpoints[0].time = time_offset
        for i in range(len(tpoints))[1:]:
            #re calc time by velocities
            tpoints[i].update_point(tpoints[i-1])

        points_timestamps = [tpoint.time for tpoint in points_timestamps]

        return tpoints, points_timestamps

    def get_spin_sector(self, robot, points, index):
        max_angular_acc = robot.max_angular_acc

        time_diff = points[index + 1]["timestamp"] - points[index]["timestamp"]
        heading_diff = utils.delta_angle(points[index + 1]["point"].heading, points[index]["point"].heading)

        max_angular_vel = (time_diff - math.sqrt(time_diff**2 - 4*abs(heading_diff)/max_angular_acc)) * max_angular_acc / 2
        acc_time =  max_angular_vel / max_angular_acc

        return ({
            "time_diff": time_diff,
            "heading_diff": heading_diff,
            "max_angular_vel": max_angular_vel,
            "acc_time": acc_time,
            "start_time": points[index]["timestamp"],
            "end_time": points[index + 1]["timestamp"]
        })

    def find_spin_sectors(self, points_timestamps, robot):
        # TODO: Move timestamps into the points objects
        points = [{
            "point": self.points[index],
            "timestamp": points_timestamps[index]
        } for index in range(len(self.points)) if (self.points[index].use_heading) ]

        spin_sectors = [
            self.get_spin_sector(robot, points, index)
            for index in range(len(points) - 1)
        ]

        return spin_sectors

    def find_trajectory(self, robot, time_offset):
        tpoints, points_timestamps = self.find_basic_trajectory(robot, time_offset)

        points_timestamps[0] = tpoints[0].time + self.DELAY_OMEGA
        points_timestamps[-1] = tpoints[-1].time - self.DELAY_OMEGA

        spin_sectors = self.find_spin_sectors(points_timestamps, robot)

        max_angular_vel = max([sec["max_angular_vel"] for sec in spin_sectors])

        robot_radius = ((robot.width / 2)**2 + (robot.height / 2)**2)**0.5
        max_linear_by_angular = max_angular_vel * robot_radius
        original_max_vel = robot.max_vel

        robot.max_vel *= robot.max_vel / (robot.max_vel + max_linear_by_angular)

        # Recalculate trajectory given new max linear velocity defined by the angular velocity
        tpoints, points_timestamps = self.find_basic_trajectory(robot, time_offset)

        points_timestamps[0] = tpoints[0].time + self.DELAY_OMEGA
        points_timestamps[-1] = tpoints[-1].time - self.DELAY_OMEGA

        spin_sectors = self.find_spin_sectors(points_timestamps, robot)

        #interpolate to cycle time
        traj = [trajectory_point(tpoints[0].x, tpoints[0].y, tpoints[0].angle, self.points[0].heading)]
        t = 0
        cycle = (robot.cycle/1000.0) #s
        #calc bias to make sure the last point is when V=0
        bias = tpoints[-1].time - math.floor(tpoints[-1].time/cycle)*cycle
        traj[0].time = time_offset

        for i in range(len(tpoints))[1:]:
            p_time = (t+1)*cycle+time_offset+bias
            while ((p_time <= tpoints[i].time) and (p_time >= tpoints[i-1].time)):
                t += 1

                traj.append(trajectory_point(tpoints[i].x, tpoints[i].y, tpoints[i].angle))

                dt  = tpoints[i].time-tpoints[i-1].time
                dv = (tpoints[i].vel - tpoints[i-1].vel)/dt
                dx  = (tpoints[i].x - tpoints[i-1].x)/dt
                dy  = (tpoints[i].y - tpoints[i-1].y)/dt
                da  = (utils.delta_angle(tpoints[i].angle, tpoints[i-1].angle))/dt
                traj[t].x = dx*p_time - dx*tpoints[i-1].time + tpoints[i-1].x
                traj[t].y = dy*p_time - dy*tpoints[i-1].time + tpoints[i-1].y
                traj[t].angle = (da*p_time - da*tpoints[i-1].time + tpoints[i-1].angle) % (2*math.pi)
                traj[t].vel = dv*p_time - dv*tpoints[i-1].time + tpoints[i-1].vel
                traj[t].acc = (traj[t].vel - traj[t-1].vel)/cycle
                traj[t].time = p_time
                traj[t].slow = tpoints[i-1].slow
                traj[t].slow_no_cam = tpoints[i-1].slow_no_cam
                traj[t].vx = traj[t].vel * math.cos(traj[t].angle)
                traj[t].vy = traj[t].vel * math.sin(traj[t].angle)

                p_time = (t+1)*cycle+time_offset+bias

        traj_index = 1
        sector_index = 0
        sector_time = tpoints[0].time
        was_in_sector = False

        while (traj_index < len(traj)):
            if sector_index < len(spin_sectors) and spin_sectors[sector_index]["start_time"] <= sector_time <= spin_sectors[sector_index]["end_time"]:
                sector = spin_sectors[sector_index]

                max_angular_vel = sector["max_angular_vel"]
                time_diff = sector["time_diff"]
                acc_time = sector["acc_time"]

                was_in_sector = True

                spin_time = sector_time - sector["start_time"]

                if spin_time < acc_time:
                    curr_vel = spin_time * robot.max_angular_acc
                elif spin_time < time_diff - acc_time:
                    curr_vel = max_angular_vel
                else:
                    curr_vel = max_angular_vel - (spin_time - time_diff + acc_time) * robot.max_angular_acc

                traj[traj_index].heading = traj[traj_index-1].heading + utils.sign(sector["heading_diff"])*curr_vel*cycle

                if (traj_index >= 2):
                    traj[traj_index].wheading = utils.delta_angle(traj[traj_index].heading, traj[traj_index-2].heading) / (cycle * 2)
                else:
                    traj[traj_index].wheading = 0
            else:
                if (was_in_sector):
                    sector_index += 1
                    was_in_sector = False

                traj[traj_index].heading = traj[traj_index - 1].heading
                traj[traj_index].wheading = 0

            traj_index += 1
            sector_time += cycle

        robot.max_vel = original_max_vel

        self.trajectory = traj

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

    def create_path_data(self):
        xs, ys = self.draw_graph(0.001)
        path_points = []
        for i in range(len(xs)):
            path_points.append({"x":xs[i], "y":ys[i]})
        data = {"path_points": path_points,"traj": self.create_traj_data(), "costs": self.costs, "scalars_x": list(np.ravel(self.scalars_x)), "scalars_y": list(np.ravel(self.scalars_y))}
        return data

    def create_traj_data(self):
        data = {'time':[], 'x':[], 'y':[], 'vel':[], 'vx':[], 'vy':[], 'acc':[], 'heading':[], 'wheading':[], 'slow':[]}
        for tpoint in self.trajectory:
            data["time"].append(tpoint.time)
            data["x"].append(tpoint.x)
            data["y"].append(tpoint.y)
            data["slow"].append(tpoint.slow)
            data["vel"].append(tpoint.vel)
            data["vx"].append(tpoint.vx)
            data["vy"].append(tpoint.vy)
            data["acc"].append(tpoint.acc)
            data["heading"].append(tpoint.heading)
            data["wheading"].append(tpoint.wheading)

        return data

def main(data_from_js):
    paths = []
    out_data  = {'path':[], 'traj':{}}
    out_data['traj'] = {'time':[], 'x':[], 'y':[], 'vel':[], 'vx': [], 'vy': [], 'acc':[], 'heading':[], 'wheading':[], 'slow':[]}
    parsed_from_js = json.loads(data_from_js)

    in_data = parsed_from_js['data']
    cmd = parsed_from_js['cmd']

    #set up path_finder objects
    for index, path_data in enumerate(in_data):
        path_points = [utils.Point(
            path_point["x"],
            path_point["y"],
            path_point["direction"],
            path_point["heading"],
            path_point["start_mag"],
            path_point["end_mag"],
            path_point["p_vel"],
            path_point["use_heading"]
        ) for path_point in path_data["points"]]

        paths.append(path_finder(
            path_data["params"],
            path_data["scalars_x"],
            path_data["scalars_y"],
            path_data["slow_start"],
            path_data["slow_end"],
            *path_points))

    #setup robot object
    robot = utils.Robot(path_data["params"])

    time_offset = 0

    for path in paths:
        #the reason we are all here:
        if (cmd == 0):
            path.find_scalars()

        path.find_trajectory(robot, time_offset)

        #set data to be sent to GUI
        out_data["path"].append(path.create_path_data())
        out_data["traj"] = utils.merge_dicts(out_data["traj"], path.create_traj_data())

        time_offset = path.trajectory[-1].time

    print('#' + json.dumps(out_data))

    #set this to True to open matplotlib for graphing
    if True:
        for path in paths:
            tpoints = path.trajectory

        vx  = []
        vy = []
        times = []
        headings = []

        dts = []

        sim_x, sim_y = [tpoints[0].x], [tpoints[0].y]

        for i in range(len(tpoints)):
            vx.append(tpoints[i].vx)
            vy.append(tpoints[i].vy)
            headings.append(tpoints[i].heading)

            vel = math.sqrt(vx[i]**2 + vy[i]**2)
            #sim_head = tpoints[i].angle

            if (i < len(tpoints) -1):
                dt = (tpoints[i+1].time-tpoints[i].time)

                sim_x.append(sim_x[i-1] + vx[i])
                sim_y.append(sim_y[i-1] + vy[i])
                dts.append(tpoints[i+1].time-tpoints[i].time)

            times.append(tpoints[i].time)

        fig = plt.figure(figsize=(9, 5),dpi=80)
        fig.canvas.set_window_title('Trajectory Graphs')

        traj_p = plt.subplot (3, 1, 1)
        acc_p  = plt.subplot (3, 1, 2)
        path_p = plt.subplot (3, 2, 5)
        dsdt_p = plt.subplot (3, 2, 6)

        # acc_p.plot(times, headings)
        acc_p.plot(times, np.gradient(headings))
        acc_p.set(xlabel='', ylabel='Heading')
        acc_p.grid()

        traj_p.plot(times, vy, label='vx')
        traj_p.plot(times, vx, label='vy')
        handles, labels = traj_p.get_legend_handles_labels()
        traj_p.legend(handles, labels)
        traj_p.set(xlabel='', ylabel='Velocity [m/s]')
        traj_p.grid()

        #path_p.scatter(paths[0].draw_graph(0.001)[0], paths[0].draw_graph(0.001)[1], s=3)
        path_p.plot(paths[0].draw_graph(0.001)[0], paths[0].draw_graph(0.001)[1])
        #path_p.plot(sim_x, sim_y)
        path_p.set(xlabel='X [m]', ylabel='Y [m]')
        path_p.axis('equal')
        path_p.grid()

        dsdt_p.plot(times[:-1], dts)
        dsdt_p.set(xlabel='time', ylabel='ds/dt [S/s]')
        dsdt_p.grid()

        plt.show()
        plt.close('all')

if __name__ == "__main__":
    main(sys.argv[1])

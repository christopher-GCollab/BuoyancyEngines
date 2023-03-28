# Descrete time domain modeling of a buoyancy engine
# To do:
# - Send mission as array of length 2 arrays - ((buoyancy, duration), (buoyancy, duration))
# - create algorthm or proportional tuning that gets volume level needed for depth
# - or something that can pump and guess when to reach depth???
# - current depth vs set point depth gives error, multiply by 

# https://www2.hawaii.edu/~zsong/rauv-icra2019/papers/ARMR-DSR_2019_paper_4_final.pdf
# https://naomi.princeton.edu/wp-content/uploads/sites/744/2021/03/jggraver-thesis-4-11-05.pdf
# https://www.mdpi.com/2075-1702/10/5/381

def getCubicMFromLitres(liters):
    return liters/1000

def getLitersFromCubicM(m3):
    return m3*1000

def getLitersFromFluidLevel(percentage):
    # Calculate litres of fluid in the bladder from reservoir fluid level.
    liters = 100 * percentage
    return liters

def fluidLevelToLitres(percentage, maxPumpFluid):
    liters = percentage * maxPumpFluid
    return liters

def getPumpStatus():
    # Checks pump status level
    pumpStatus = 0
    return pumpStatus

# def getPumpFluidLevel(i, duration):
#     # This is a crappy simulation of different pump positions by time
#     # Return fluid level based on total duration
#     if 0 <= i / duration < 0.25:
#         # print("here")
#         fluidLevel = 0.4

#     elif 0.25 <= i / duration < 0.5:
#         fluidLevel = 0.2
    
#     elif 0.5 <= i / duration < 0.75:
#         fluidLevel = 0.5
    
#     elif 0.75 <= i / duration < 1:
#         fluidLevel = 0.6
#     # fluidLevel = 0.2
#     return fluidLevel

def getPumpFluidLevel(fluidLevel, depth_current, depth_target, dt):
    # Return a percentage of the bladder/pump reservoir amount filled
    error = depth_target - depth_current # negative means you need to sink
    # print(error)
    if error < 0 and fluidLevel > 0:
        # Above depth target, need to sink.
        fluidLevel -= drainRate * dt
    elif error > 0 and fluidLevel < 1:
        # Below depth tarket, need to float.
        fluidLevel += pumpRate * dt
    else:
        return fluidLevel
    # print(fluidLevel)
    return fluidLevel 

class BuoyEng:
    def __init__(self):
        self.g = 9.81 # gravity | m/s/s
        # self.rho = 1025 # fluid density | kg/m3
        self.area = 0.25*np.pi*0.5**2 # characteristic area | m2
        self.cd = 1.28 # drag coefficient | dimensionless
        self.m_sys = 200 # system wet mass | kg

        self.vol_set = getCubicMFromLitres(6.) # Liters
        
        self.buoyancy = 0.
        self.drag = 0.
        self.vol = 0.
        self.acc = 0.
        self.vel = 0.
        self.depth = 0.

    
    def calc_density(self):
        # density = polyfit density @ depth with column profile data
        self.density = 1025
        return self.density
    
    def get_vol(self, vol_L):
        self.vol = getCubicMFromLitres(vol_L)
        return self.vol
    
    def calc_dVol(self):
        # Returns volume of displaced fluid from neutral/set buoyancy.
        # current volume 8L - 6L set should be positive
        self.dVol =  self.vol - self.vol_set
        return self.dVol

    def calc_drag(self):
        # Return drag force
        self.drag = 0.5 * self.density * self.area * self.cd * np.square(self.vel)
        return self.drag
    
    def calc_buoyancy(self):
        self.buoyancy = self.density * self.g * self.dVol
        return self.buoyancy

    def calc_acc(self):
        # Calculates acceleration by balance the buoyancy force and drag force divided by mass
        # Returns accerlation
        if self.buoyancy <= 0:
            self.acc = (self.buoyancy + self.drag) / self.m_sys
        else:
            self.acc = (self.buoyancy - self.drag) / self.m_sys
        # print(self.acc)
        return self.acc
    

    def calc_vel(self, dt):
        # Returns Velcoity
        self.vel += self.acc * dt # standard euler method

        return self.vel

    def calc_depth(self, dt):
        # Returns Depth
        self.depth += self.vel*dt - 0.5*self.acc*np.square(dt)
        return self.depth

    def updateAll(self, dt, vol_L):
        self.calc_density()
        self.get_vol(vol_L)
        self.calc_dVol()
        self.calc_drag()
        self.calc_buoyancy()
        self.calc_acc()
        self.calc_vel(dt)
        self.calc_depth(dt)

        # print(self.vol)
        # print(self.dVol)
        # print(self.drag)
        # print(self.buoyancy)
        # print(self.acc)
        # print(self.vel)
        # print(self.depth)
        
import numpy as np
import matplotlib.pyplot as plt

# Plotting ------------------------
az = [] # Acceleration 
vz = [] # Velocity
xz = [] # Displayment / Depth
f_buoyancy = [] # Buoyancy Force | N
f_drag = [] # Drag force | N
time = [] # Time | seconds
dVolume = []
bladderVolume = []
plt_fluidLevel = []
plt_depthTarget = []

# Looping ------------------------
i = 0   # Start | seconds
dt = 0.00001 # Timestep |seconds
sea_surface = 0 # Depth/height | meters
commandInterval = 1 #
duration = 200 # Sim duration | seconds #84 seconds shows - it's unstable

# Parameters ------------------------
maxPumpFluid = 12 
fluidLevel = 0.2
depth_current = 0
depth_target = -20
pumpRate = 0.01 # Pumping rate (float) | Liters/second
drainRate = 0.05 # Drain rate (sink) | Liters/second

# Initial Conditions ------------------------
# vol_L = 8.
pumpStatus = 0 # Pump on (1) | Pump Holding (0) | Pump draining (-1)

buoyEng = BuoyEng()

while i < duration:
    # if (i % commandInterval) == 0:
    #     pumpFluidLevel = getPumpFluidLevel(i, duration)
    #     vol_L = fluidLevelToLitres(pumpFluidLevel, maxPumpFluid)
    # pumpFluidLevel = getPumpFluidLevel(i, duration)
    
    fluidLevel = getPumpFluidLevel(fluidLevel, depth_current, depth_target, dt)
    vol_L = fluidLevelToLitres(fluidLevel, maxPumpFluid)
    
    buoyEng.updateAll(dt, vol_L)
    depth = buoyEng.depth
    vel = buoyEng.vel
    acc = buoyEng.acc
    buoyEng.updateAll(dt, vol_L) # run second time to predict
    depth = depth + (depth + buoyEng.depth)/2

    if buoyEng.depth > sea_surface:
        # Break loop when engine has reached surface
        break

    xz.append(buoyEng.depth)
    vz.append(buoyEng.vel)
    az.append(buoyEng.acc)
    f_buoyancy.append(buoyEng.buoyancy)
    f_drag.append(buoyEng.drag)
    dVolume.append(getLitersFromCubicM(buoyEng.dVol))
    bladderVolume.append(getLitersFromCubicM(buoyEng.vol))
    time.append(i)
    plt_fluidLevel.append(fluidLevel)
    plt_depthTarget.append(depth_target)

    depth_current = buoyEng.depth
    i = i + dt    

# -----------------------------------------
fig, (ax1, ax2, ax3, ax4, ax5, ax6, ax7) = plt.subplots(7, figsize=(8, 8), sharex=True)
# fig.suptitle('Buoyancy Engine')

ax1.plot(time, xz, label = 'Depth')
ax1.plot(time, plt_depthTarget, 'r')
ax1.grid(True)
ax1.set_ylabel('Depth (m)')

ax2.plot(time, vz)
ax2.grid(True)
ax2.set_ylabel('Vel (m/s)')

ax3.plot(time, az)
ax3.grid(True)
ax3.set_ylabel('Acc (m/s/s)')

ax4.plot(time, f_buoyancy)
ax4.grid(True)
ax4.set_ylabel('Buoyancy (N)')

ax5.plot(time, f_drag)
ax5.grid(True)
ax5.set_ylabel('Drag (N)')

ax6.plot(time, dVolume)
ax6.plot(time, bladderVolume, 'r')
ax6.grid(True)
ax6.set_ylabel('Volume (L)')

ax7.plot(time, plt_fluidLevel)
ax7.grid(True)
ax7.set_ylabel('Fluid Level')

plt.xlabel('Time (s)')
plt.tight_layout()
# plt.show(block = False)
plt.show()
# -----------------------------------------

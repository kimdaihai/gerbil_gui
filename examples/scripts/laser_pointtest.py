# my cnctoolbox script!
#
c = compiler
t = gcodetools
grbl = self.grbl

focus_range = 20
dir = 1
width = 100
point_distance = 5
points_per_line = int(width/point_distance)

self.new_job()
gcodes = []
gcodes.append("G91") # relative distances

# turn laser off
gcodes.append("S0")
gcodes.append("M3")

gcodes.append("G0 Z{}".format(-focus_range / 2)) # first movement down

# first row = 50 ms, each row plus 50ms
for dwell in range(0, 10000, 500):
    dwell += 500
    gcodes.append("S255")
    gcodes.append("G4 P{:0.2f}".format(dwell/10000))
    gcodes.append("S0")
    for x in range(1, points_per_line + 1):
        z_inc = focus_range / points_per_line
        gcodes.append("G0 X{} Z{}".format(point_distance * dir, z_inc * dir))
        gcodes.append("S255")
        gcodes.append("G4 P{:0.2f}".format(dwell/10000))
        gcodes.append("S0")
    gcodes.append("G0 Y{}".format(point_distance))
    dir *= -1

# turn laser off
gcodes.append("S0")
gcodes.append("M3")

self.grbl.preprocessor.do_fractionize_arcs = False
self.grbl.preprocessor.do_fractionize_lines = False
self.grbl.write(gcodes)

self.set_target("simulator")
self.job_run()














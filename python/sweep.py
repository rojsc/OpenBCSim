# -*- coding: future_fstrings -*-

import numpy as np
from pyrfsim import RfSimulator
import argparse
from scipy.signal import gausspulse
from time import time
import h5py
import matplotlib.pyplot as plt

description="""
    Simulate using scatterers from hdf file.
    Scan type is a linear scan in the XZ plane.
    
    This script is also useful for measuring
    the simulation time over a number of equal
    runs.
"""

def do_simulation(args):
    if args.use_gpu:
        sim = RfSimulator("gpu")
        sim.set_parameter("gpu_device", "%d"%args.device_no)
        gpu_name = sim.get_parameter("cur_device_name")
        print "Using device %d: %s" % (args.device_no, gpu_name)
    else:
        sim = RfSimulator("cpu")

    sim.set_parameter("verbose", "0")

    with h5py.File(args.h5_file, "r") as f:
        scatterers_data = f["data"][()]
    sim.add_fixed_scatterers(scatterers_data)
    print "The number of scatterers is %d" % scatterers_data.shape[0]

    # configure simulation parameters
    sim.set_parameter("sound_speed", "1540.0")
    sim.set_parameter("radial_decimation", "10")
    sim.set_parameter("phase_delay", "on")
    sim.set_parameter("noise_amplitude", "%f" % args.noise_ampl)

    # configure the RF excitation
    fs = 80e6
    ts = 1.0/fs
    fc = 5.0e6
    tc = 1.0/fc
    t_vector = np.arange(-16*tc, 16*tc, ts)
    bw = 0.3
    samples = np.array(gausspulse(t_vector, bw=bw, fc=fc), dtype="float32")
    center_index = int(len(t_vector)/2) 
    sim.set_excitation(samples, center_index, fs, fc)

    # configure the beam profile
    sim.set_analytical_beam_profile(1e-3, 1e-3)

    for i, y in enumerate(np.linspace(-0.005, 0.005, 100)):
        print(f"Simulating frame {i}")
        # define the scan sequence
        origins = np.zeros((args.num_lines, 3), dtype="float32")
        origins[:,1] = y
        origins[:,0] = np.linspace(args.x0, args.x1, args.num_lines)
        x_axis = np.array([1.0, 0.0, 0.0])
        z_axis = np.array([0.0, 0.0, 1.0])
        directions = np.array(np.tile(z_axis, (args.num_lines, 1)), dtype="float32")
        length = 0.06
        lateral_dirs = np.array(np.tile(x_axis, (args.num_lines, 1)), dtype="float32")
        timestamps = np.zeros((args.num_lines,), dtype="float32")
        sim.set_scan_sequence(origins, directions, length, lateral_dirs, timestamps)

        iq_lines = sim.simulate_lines()
        bmode = np.array(abs(iq_lines), dtype="float32")
        gain = 1
        dyn_range = 40
        normalize_factor = np.max(bmode.flatten())
        bmode = 20*np.log10(gain*bmode/normalize_factor)
        bmode = 255.0*(bmode+dyn_range)/dyn_range
        # clamp to [0, 255]
        bmode[bmode < 0]     = 0.0
        bmode[bmode > 255.0] = 255.0

        fig = plt.figure(frameon=False)
        fig.set_size_inches(2*bmode.shape[1], bmode.shape[0])
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)
        ax.imshow(np.real(abs(iq_lines)), aspect="auto", cmap=plt.get_cmap("gray"))
        plt.savefig(f"sweep_{i:02d}.png", dpi=1)
        plt.close(fig)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("h5_file", help="Hdf5 file with scatterers")
    parser.add_argument("--x0", help="Left scan width", type=float, default=-1e-2)
    parser.add_argument("--x1", help="Right scan width", type=float, default=1e-2)
    parser.add_argument("--num_lines", type=int, default=192)
    parser.add_argument("--device_no", help="GPU device no to use", type=int, default=0)
    parser.add_argument("--use_gpu", action="store_true")
    parser.add_argument("--noise_ampl", help="Simulator noise", type=float, default=0)
    args = parser.parse_args()
    
    do_simulation(args)

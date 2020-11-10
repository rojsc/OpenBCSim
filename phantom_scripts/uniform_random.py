import numpy as np
import h5py
import argparse

description="""
Create scatterers uniformly distributed in an axis-aligned box. By default,
this box is 0.1 x 0.1 x 0.1 m large and centered around the origin. For
reproducability, use the --seed argument to define a RNG seed manually.
"""

def create_phantom(args):
    if args.seed != -1:
        np.random.seed(args.seed)
    data = np.float32(np.random.uniform(low=(args.xmin, args.ymin, args.zmin, 0.0),
            high=(args.xmax, args.ymax, args.zmax, 1.0),
            size=(args.num_scatterers, 4)))

    with h5py.File(args.h5_file, "w") as f:
        f["data"] = data
    print "Dataset written to %s" % args.h5_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("h5_file", help="Name of scatterer hdf5 file")
    parser.add_argument("--num_scatterers", type=int, default=1000000)
    parser.add_argument("--seed", type=int, default=-1)
    parser.add_argument("--xmin", type=float, default=-0.05)
    parser.add_argument("--xmax", type=float, default=0.05)
    parser.add_argument("--ymin", type=float, default=-0.05)
    parser.add_argument("--ymax", type=float, default=0.05)
    parser.add_argument("--zmin", type=float, default=0)
    parser.add_argument("--zmax", type=float, default=0.1)
    args = parser.parse_args()

    create_phantom(args)


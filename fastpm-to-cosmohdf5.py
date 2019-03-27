"""

Convert FastPM legacy format to cosmohdf5.

Eventually this will be broken into two files, one to create the cosmohdf5 header,
and another simple file that just blindly convert the file.

The future version of FastPM will directory write the cosmohdf5 metadata schema.
"""

from argparse import ArgumentParser
import bigfile
import numpy
import os
import h5py

ap = ArgumentParser()
ap.add_argument('source', help='CosmoHDF5 snapshot files')
ap.add_argument('dest', help='Gadget filename base; dir will be created on the fly. ')
ap.add_argument('--nperfile', type=int, default=1024 * 1024, help='Number of particles per gadget file')

def write_block(block, ff):
    b = block.size * block.dtype.itemsize

    assert b < 2 * 1024 * 1024 * 1024 # avoid overflow!

    b = numpy.array(b, dtype='i4')
    b.tofile(ff)
    block.tofile(ff)
    b.tofile(ff)

def write_gadget_1_ic(filename, attrs, pos, vel, id):

    with h5py.File(filename, 'w') as ff:
        header = ff.create_dataset("Header", data=numpy.zeros(0))
        for key in attrs:
            header.attrs[key] = attrs[key]

        ff.create_group('Matter')
        ff.create_dataset('Matter/Position', data=pos)
        ff.create_dataset('Matter/Velocity', data=vel)
        ff.create_dataset('Matter/ParticleID', data=id)

def convert_header(header):
    attrs = {}
    attrs['H0'] = header.attrs['HubbleParam'][0] * 100.
    attrs['BoxSize'] = header.attrs['BoxSize'][0]
    a = header.attrs['Time'][0]
    attrs['InitialRedshift'] = 1 / a - 1
    attrs['Redshift'] = 1 / a - 1
    attrs['ParticleMass.Matter'] = header.attrs['MassTable'][1]
    attrs['NP.Matter'] = header.attrs['TotNumPart'][1]
    attrs['Omega_M'] = header.attrs['OmegaM']
    attrs['Omega_DE'] = header.attrs['OmegaLambda']
    attrs['GrowthRatio'] = header.attrs['GrowthFactor']
    attrs['f_growth']   header.attrs['GrowthRate']
    attrs['HubbleNow'] = header.attrs['HubbleE'] * header.attrs['HubbleParam'] * 100.
    attrs['RSDFactor'] = header.attrs['RSDFactor']

    return attrs

def main(ns):

    f = bigfile.File(ns.source)
    ds = bigfile.Dataset(f['1/'], ['Position', 'Velocity', 'ID'])

    header = f['Header']
    print("---input file : %s -----", ns.source)
    
    attrs = convert_header(header)

    dirname = os.path.dirname(os.path.abspath(ns.dest))
    if not os.path.exists(dirname):
        print("making dir")
        os.makedirs(dirname)

    convert(ns.dest, attrs, ds)

def convert(basename, baseattrs, ds):

    print('total number of dm particles', ds.size)

    Nfile = max(ds.size // ns.nperfile, 1)
    baseattrs['NumFilesPerSnapshot'] = Nfile

    for i in range(Nfile):
        print('working on file %d/%d' % (i, Nfile))

        start = i * ds.size // Nfile
        end = (i + 1) * ds.size // Nfile

        # read
        data = ds[start:end]
        pos = data['Position']

        vel = data['Velocity'] # peculiar velocity
        id = data['ID']

        filename = '%s.%d.hdf5' % (basename, i)

        header = baseattrs.copy()

        write_gadget_1_ic(filename, header, pos, vel, id)

if __name__ == '__main__':
    ns = ap.parse_args()
    main(ns)

""" This script converts a DESI CosmoSIM WG's HDF5 snapshot to a Gadget-1 snapshot.

    Three blocks are converted, position, velocity and ParitlceID

    precision of position and velocity is controled via --precision
    ID is always 8 bytes long.

    The default is 1 million particles per file. Change it to something bigger

    This file is minimally modified from bigfile-to-gadget-1.py from FastPM.

"""

from argparse import ArgumentParser
import cosmohdf5 as bigfile
import os
import numpy

ap = ArgumentParser()
ap.add_argument('source', help='CosmoHDF5 snapshot files')
ap.add_argument('dest', help='Gadget filename base; dir will be created on the fly. ')
ap.add_argument('--nperfile', type=int, default=1024 * 1024, help='Number of particles per gadget file')
ap.add_argument('--precision', default='f4', help='precision of floats; id is always u8')

DefaultHeaderDtype = [
        ('Npart', ('u4', 6)),
        ('Massarr', ('f8', 6)),
        ('Time', ('f8')),
        ('Redshift', ('f8')),
        ('FlagSfr', ('i4')),
        ('FlagFeedback', ('i4')),
        ('Nall', ('u4', 6)),
        ('FlagCooling', ('i4')),
        ('NumFiles', ('i4')),
        ('BoxSize', ('f8')),
        ('Omega0', ('f8')),
        ('OmegaLambda', ('f8')),
        ('HubbleParam', ('f8')),
        ('FlagAge', ('i4')),
        ('FlagMetals', ('i4')),
        ('NallHW', ('u4', 6)),
        ('flag_entr_ics', ('i4')),
    ]

def write_block(block, ff):
    b = block.size * block.dtype.itemsize

    assert b < 2 * 1024 * 1024 * 1024 # avoid overflow!

    b = numpy.array(b, dtype='i4')
    b.tofile(ff)
    block.tofile(ff)
    b.tofile(ff)

def write_gadget_1_ic(filename, header, pos, vel, id):

    with open(filename, 'wb+') as ff:
        write_block(pad256(header), ff)
        write_block(pos, ff)
        write_block(vel, ff)
        write_block(id, ff)

def make_gadget_header(header):
    attrs = header.attrs
    gadget = numpy.zeros((), dtype=DefaultHeaderDtype)
    gadget['Time']  = 1 / (attrs['Redshift'] + 1)
    gadget['Redshift']  = attrs['Redshift']
    #FIXME: file seems to be broken. NP.Matter should be a scaler.
    nall = numpy.array([0, sum(attrs['NP.Matter']), 0, 0, 0, 0], dtype='u8')
    gadget['Nall'] = numpy.uint32(nall)
    gadget['NallHW'] = numpy.uint32(nall >> 32)
    gadget['BoxSize'] = attrs['BoxSize']
    gadget['HubbleParam'] = attrs['H0'] / 100.
    gadget['Omega0'] = attrs['Omega_M']
    gadget['OmegaLambda'] = attrs['Omega_DE']
    gadget['Massarr'] = [0, attrs['ParticleMass.Matter'], 0, 0, 0, 0]

    return gadget

def pad256(gadget):
    hdtype_padded = numpy.dtype([
                                 ('header', gadget.dtype),
                                 ('padding', ('u1', 256 - gadget.dtype.itemsize))])
    data = numpy.zeros((), dtype=hdtype_padded)
    data['header'] = gadget
    assert data.dtype.itemsize == 256
    return data

def main(ns):

    f = bigfile.File(ns.source)
    ds = bigfile.Dataset(f['Matter/'], ['Position', 'Velocity', 'ParticleID'])

    header = f['Header']
    print("---input file : %s -----", ns.source)
    for key in header.attrs:
        print(key, header.attrs[key])

    gadget_header = make_gadget_header(header)

    dirname = os.path.dirname(os.path.abspath(ns.dest))
    if not os.path.exists(dirname):
        print("making dir")
        os.makedirs(dirname)

    convert(ns.dest, gadget_header, ds, ns.precision)

def convert(basename, baseheader, ds, precision):

    print('total number of dm particles', ds.size)

    Nfile = max(ds.size // ns.nperfile, 1)
    baseheader['NumFiles'] = Nfile
    a = baseheader['Time']

    for i in range(Nfile):
        print('working on file %d/%d' % (i, Nfile))

        start = i * ds.size // Nfile
        end = (i + 1) * ds.size // Nfile

        # read
        data = ds[start:end]
        pos = data['Position']
        pos = numpy.array(pos, dtype=precision)

        # convert to gadget 1 units from pecuiliar velocity
        vel = data['Velocity'] * a ** -0.5
        vel = numpy.array(vel, dtype=precision)
        id = data['ParticleID']

        filename = '%s.%d' % (basename, i)

        header = baseheader.copy()
        header['Npart'][1] = end - start
        print("header", header)
        write_gadget_1_ic(filename, header, pos, vel, id)

if __name__ == '__main__':
    ns = ap.parse_args()
    main(ns)

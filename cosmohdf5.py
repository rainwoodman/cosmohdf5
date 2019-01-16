"""
An abstract reading interface for striped cosmohdf5 snapshot files.

Requires h5py, numpy, and glob.

Here is a full example

.. code :: python

    file = File(['cosmohdf5-v1.*.hdf5']

    print(file['Header'].attrs)

    ds = Dataset(file['Matter/'], ['Velocity', 'Position'])

    print(ds.size)
    print(ds.dtype)
    print(ds[0:10])

"""

import h5py
import numpy
import glob

class File:
    def __init__(self, paths, dataset='/'):
        """ An abstact representation of a sequence of cosmohdf5 files.


            Parameters
            ----------
            paths : string or list.
                If a list, then it shall be the full list of files for the snapshot.
                If a string, it is a glob pattern (with '*' and '?') that matches against
                all files.

            dataset : string
                The root directory for getting subfiles and datasets.

            Notes
            -----

            A file object allows getting members as subfiles via the
            standard python indexing syntax. For example

            .. code :: python
                
                file['Matter/']

                file['Header']
        """
        if not isinstance(paths, (list, tuple)):
            # assume it is a string
            paths = list(glob.glob(paths))

        self.paths = paths
        self.dataset = dataset

        dg = self.get_datagroup(0)
        # detach from the original dg:
        self.attrs = dict(dg.attrs)
        assert self.dataset in dg

        self.nfiles =  len(self.paths)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def get_datagroup(self, file_num):
        return h5py.File(self.paths[file_num])[self.dataset]

    def __getitem__(self, item):
        return File(self.paths, self.dataset + '/' + item)

class Dataset:
    def __init__(self, file, columns):
        """
            Viewing certain columns from a File collection as an array like object.xi

            The object support standard python slicing with 1 indexing dimension
            along the row dimension of the data.

            Only continous indexing is supported currently.

        """

        self.file = file
        dtype = []

        dg = file.get_datagroup(0)
        for cname in columns:
            column = dg[cname]
            dtype.append((cname, (column.dtype, column.shape[1:])))

        sizes = numpy.zeros((self.file.nfiles, len(columns)), dtype='i8')

        for i in range(file.nfiles):
            dg = file.get_datagroup(i)
            for j, cname in enumerate(columns):
                column = dg[cname]
                sizes[i, j] = column.shape[0]

        assert (sizes[:, 0][:, None] == sizes).all()

        self.size = int(sizes[:, 0].sum())
        self.offsets = numpy.concatenate([[0], sizes[:, 0].cumsum()])
        self.dtype = numpy.dtype(dtype)

    def _solve_intersections(self, start, end):
        first = self.offsets.searchsorted(start, side='r') - 1
        last = self.offsets.searchsorted(end, side='l')

        offset = 0
        for i in range(first, last):
            s1 = self.offsets[i]
            e1 = self.offsets[i + 1]
#            print(i, start, end, s1, e1)
            lstart, lend = max(s1, start) - s1, min(e1, end) - s1
            lsize = lend - lstart
            yield i, slice(lstart, lend), slice(offset, offset + lsize)
            offset = offset + lsize

        assert offset == end - start

    def __getitem__(self, index):
        if isinstance(index, tuple):
            # no fancier indexing
            assert len(index) == 1
            return self.__getitem__(index[0])
        if not isinstance(index, slice):
            raise IndexError("only slices are supported")

        start, end, step = index.indices(self.size)

        if step != 1:
            raise IndexError("step size of slice must be 1")

        data = numpy.empty(end - start, self.dtype)

        for filenum, lslice, gslice in self._solve_intersections(start, end):
            dg = self.file.get_datagroup(filenum)
            for cname in self.dtype.fields:
                data[cname][gslice] = dg[cname][lslice]
        return data

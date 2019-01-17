# cosmohdf5

An interface for accessing the file level striped HDF5 files carrying the
DESI cosmosim WG schema.

The schema is defined as:
```

name: "/Matter/Position", shape: (N,3), dtype: float64, units: comoving Mpc/h
name: "/Matter/Velocity", shape: (N,3), dtype: float64, units: peculiar velocity in km/s
name: "/Matter/ParticleID", shape: (N,), dtype: int64

name: "/Header", no data, only attributes:

[note: these are time-invariant quantities and some typical values]

H0 = 67.36 [units of km/s/Mpc]   [ h = H0 / 100 ]
BoxSize = 500 [units of Mpc/h]
InitialRedshift = 200
NP.Matter = 16777216000
Omega_M = 0.3137721
Omega_DE = 0.6862279
ParticleMass.Matter [units of Msun/h]
NumFilesPerSnapshot

[these vary with time/epoch]
GrowthRatio = D(z)/D(z=0) at z
f_growth = d(ln D )/ d(ln a) at z
HubbleNow = H(z), in km/s/Mpc 
RSDFactor = 1/(aH), in Mpc/(km/s) [converts peculiar velocities to comoving displacments for redshift distortion]
Redshift = 200

Values at z=200 in Abacus from the above cosmology.

GrowthRatio =  [0.006320791 ]
f_growth = [0.9999998530991349 ]
HubbleNow = [107523.5 ]
```


Currently the interface only supports reading of existing files.

Plan to add interface for creating new snapshots. This will be handy
for creating converters into this format.

After that we can add more converters to and from this format. 

Finally this will allow an application that can automatically convert from
any format to any format using the cosmohdf5 format as an intermediate representation.


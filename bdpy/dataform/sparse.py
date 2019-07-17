'''Sparse array class.

This file is a part of bdpy.
'''

__all__ = ['SparseArray', 'load_array', 'save_array']


import os

import numpy as np
import h5py
import hdf5storage


def load_array(fname, key='data'):
    '''Load an array (dense or sparse).'''

    with h5py.File(fname, 'r') as f:
        methods = [attr for attr in dir(f[key]) if callable(getattr(f[key], str(attr)))]
        if 'keys' in methods and '__bdpy_sparse_arrray' in f[key].keys():
            # SparseArray
            s_ary = SparseArray(fname, key=key)
            return s_ary.dense
        elif type(f[key].value) == np.ndarray:
            # Dense array
            return hdf5storage.loadmat(fname)[key]
        else:
            raise RuntimeError('Unsupported data type: %s' % type(f[key].value))


def save_array(fname, array, key='data', dtype=np.float64, sparse=False):
    '''Save an array (dense or sparse).'''

    if sparse:
        # Save as a SparseArray
        s_ary = SparseArray(array.astype(dtype))
        s_ary.save(fname, key=key, dtype=dtype)
    else:
        # Save as a dense array
        hdf5storage.savemat(fname,
                            {key: array.astype(dtype)},
                            format='7.3', oned_as='column',
                            store_python_metadata=True)

    return None


class SparseArray(object):
    '''Sparse array class.'''
    
    def __init__(self, src=None, key='data', background=0):
        self.__background = background

        if type(src) == np.ndarray:
            # Create sparse array from numpy.ndarray
            self.__make_sparse(src)
        elif os.path.isfile(src):
            # Load data from src
            self.__load(src, key=key)
        else:
            raise ValueError('Unsupported input')

    @property
    def dense(self):
        return self.__make_dense()

    def save(self, fname, key='data', dtype=np.float64):
        hdf5storage.savemat(fname, {key: {u'__bdpy_sparse_arrray': True,
                                          u'index': self.__index,
                                          u'value': self.__value.astype(dtype),
                                          u'shape': self.__shape,
                                          u'background' : self.__background}},
                            format='7.3', oned_as='column', store_python_metadata=True)
        return None

    def __make_sparse(self, array):
        self.__index = np.where(array != self.__background)
        self.__value = array[self.__index]
        self.__shape = array.shape
        return None

    def __make_dense(self):
        dense = np.ones(self.__shape) * self.__background
        dense[self.__index] = self.__value
        return dense

    def __load(self, fname, key='data'):
        data = hdf5storage.loadmat(fname)[key]
        self.__index = data[u'index']
        self.__value = data[u'value']
        self.__shape = data[u'shape']
        self.__background = data[u'background']
        return None

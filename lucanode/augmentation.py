"""
Utilities and classes used for dataset augmentation
"""
from abc import ABC, abstractmethod
import itertools
import collections

import numpy as np
import pandas as pd
from scipy.ndimage.interpolation import zoom
from keras.preprocessing.image import ImageDataGenerator
import cv2


class Transformer(ABC):
    def __init__(self, object):
        self.object = object

    @abstractmethod
    def apply(self, *args, **kwargs):
        pass


class FlipXTransform(Transformer):
    def apply(self, do_flip):
        """Flip an NxMxD np.array horizontally
        >>> a = np.array([[[1,2], \
                           [3,4]], \
                          [[5,6], \
                           [7,8]]])
        >>> FlipXTransform(a).apply(False)
        array([[[1, 2],
                [3, 4]],
        <BLANKLINE>
               [[5, 6],
                [7, 8]]])
        >>> FlipXTransform(a).apply(True)
        array([[[3, 4],
                [1, 2]],
        <BLANKLINE>
               [[7, 8],
                [5, 6]]])
        """
        if do_flip:
            return np.flip(self.object, axis=1)
        else:
            return self.object.copy()


class RotateTransform(Transformer):
    TRANSFORMATION = {
        0: lambda x: x,
        90: lambda x: np.flip(x, axis=1).T,
        180: lambda x: np.flip(np.flip(x, axis=0), axis=1),
        270: lambda x: np.flip(x, axis=0).T,
    }

    def apply(self, degrees):
        """Rotate an NxMxD np.array
        >>> a = np.array([[[1,2], \
                           [3,4]], \
                          [[5,6], \
                           [7,8]]])
        >>> RotateTransform(a).apply(0)
        array([[[1, 2],
                [3, 4]],
        <BLANKLINE>
               [[5, 6],
                [7, 8]]])
        >>> RotateTransform(a).apply(90)
        array([[[2, 4],
                [1, 3]],
        <BLANKLINE>
               [[6, 8],
                [5, 7]]])
        >>> RotateTransform(a).apply(180)
        array([[[4, 3],
                [2, 1]],
        <BLANKLINE>
               [[8, 7],
                [6, 5]]])
        >>> RotateTransform(a).apply(270)
        array([[[3, 1],
                [4, 2]],
        <BLANKLINE>
               [[7, 5],
                [8, 6]]])
        >>> RotateTransform(a).apply(23)
        Traceback (most recent call last):
        ...
        KeyError: 23
        """
        result = self.object.copy()
        num_dimensions = self.object.shape[0]
        for d in range(num_dimensions):
            result[d, :, :] = self.TRANSFORMATION[degrees](self.object[d, :, :])
        return result


class ZoomTransform(Transformer):
    def apply(self, factor):
        """Zoom an NxMxD np.array
        >>> a = np.array([[[ 1, 2, 3, 4], \
                           [ 5, 6, 7, 8], \
                           [ 9,10,11,12], \
                           [13,14,15,16]], \
                          [[ 0, 0, 0, 0], \
                           [ 0, 1, 1, 0], \
                           [ 0, 1, 1, 0], \
                           [ 0, 0, 0, 0]]])
        >>> ZoomTransform(a).apply(2.0)
        array([[[ 5,  6,  6,  6],
                [ 7,  8,  8,  8],
                [ 9,  9,  9, 10],
                [11, 11, 11, 12]],
        <BLANKLINE>
               [[ 1,  1,  1,  1],
                [ 1,  1,  1,  1],
                [ 1,  1,  1,  1],
                [ 1,  1,  1,  1]]])
        >>> ZoomTransform(a).apply(0.5)
        array([[[ 0,  0,  0,  0],
                [ 0,  1,  4,  0],
                [ 0, 13, 16,  0],
                [ 0,  0,  0,  0]],
        <BLANKLINE>
               [[ 0,  0,  0,  0],
                [ 0,  0,  0,  0],
                [ 0,  0,  0,  0],
                [ 0,  0,  0,  0]]])
        >>> ZoomTransform(a).apply(0.9)
        array([[[ 1,  2,  3,  4],
                [ 5,  6,  7,  8],
                [ 9, 10, 11, 12],
                [13, 14, 15, 16]],
        <BLANKLINE>
               [[ 0,  0,  0,  0],
                [ 0,  1,  1,  0],
                [ 0,  1,  1,  0],
                [ 0,  0,  0,  0]]])
        """
        result = np.zeros(self.object.shape, self.object.dtype)
        num_dimensions = self.object.shape[0]
        zoomed = np.array([zoom(self.object[d, :, :], factor) for d in range(num_dimensions)])
        input_shape = np.array(result.shape[1:])
        zoomed_shape = np.array(zoomed.shape[1:])
        offset = np.abs((input_shape - zoomed_shape) // 2).astype(np.int32)
        if factor < 1:
            short = zoomed
        else:
            short = result
        h_mi = offset[0]
        h_ma = offset[0] + short.shape[1]
        w_mi = offset[1]
        w_ma = offset[1] + short.shape[2]
        if factor < 1:
            result[:, h_mi:h_ma, w_mi:w_ma] = zoomed[:, :, :]
        else:
            result[:, :, :] = zoomed[:, h_mi:h_ma, w_mi:w_ma]
        return result


class DisplacementTransform(Transformer):
    def apply(self, displacement):
        pass


class LaplacianTransform(Transformer):
    def apply(self, do_laplacian):
        """Apply a Laplacian of gaussians on the object"""
        if do_laplacian:
            slice_with_laplacian = self.object[0, :, :] - cv2.Laplacian(self.object[0, :, :].astype(np.float32),
                                                                        cv2.CV_32F)
            filtered_object = self.object.copy()
            filtered_object[0, :, :] = slice_with_laplacian
            return filtered_object
        else:
            return self.object.copy()


TRANSFORMATIONS = {
    "flip": {"class": FlipXTransform, "values": [False, True]},
    "rotate": {"class": RotateTransform, "values": [0, 90, 180, 270]},
    "zoom": {"class": ZoomTransform, "values": [0.9, 1.0, 1.1]},
    "laplacian": {"class": LaplacianTransform, "values": [True]},
}


def apply_chained_transformations(data, transformations, available_transformations=TRANSFORMATIONS):
    for k, v in transformations.items():
        if k not in available_transformations:
            continue
        transformation_class = available_transformations[k]["class"]
        if not isinstance(v, collections.Iterable):
            v = [v]
        data = transformation_class(data).apply(*v)
    return data


def _merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def _augment_transformations(transformations):
    """Augments transformations by doing the cartesian product between them.

    >>> t = {"flip"  : {"values": [0, 1]}, \
             "rotate": {"values": [0, 90]} }
    >>> list(_augment_transformations(t))
    [{'flip': 0, 'rotate': 0}, {'flip': 0, 'rotate': 90}, {'flip': 1, 'rotate': 0}, {'flip': 1, 'rotate': 90}]
    """
    def transformations_values(name, values):
        for v in values:
            yield {name: v}

    generators = [transformations_values(k, v["values"]) for k, v in transformations.items()]
    transformations_cartesian_generator = (_merge_dicts(*e) for e in itertools.product(*generators))
    return transformations_cartesian_generator


def augment_dataframe(df, transformations=TRANSFORMATIONS):
    """
    Performs the cartesian product between df and transformations, which will later be used for data augmentation
    :param df: Pandas DataFrame
    :param transformations: transformation dict with augmentation, like TRANSFORMATIONS
    :return: Pandas DataFrame augmented with new transformation columns

    >>> t = {"flip"  : {"values": [0, 1]}, \
             "rotate": {"values": [0, 90]} }
    >>> df = pd.DataFrame([{'a': 0}, {'a': 1}])
    >>> augment_dataframe(df, t)
       a  flip  rotate
    0  0     0       0
    1  0     0      90
    2  0     1       0
    3  0     1      90
    4  1     0       0
    5  1     0      90
    6  1     1       0
    7  1     1      90
    """
    generator = (_merge_dicts(*e)
                 for e in itertools.product(df.to_dict('records'), _augment_transformations(transformations)))
    return pd.DataFrame(generator)


def crop_to_shape(arr, shape, cval=0):
    """Crops a numpy array into the specified shape. If the array was larger, return centered crop. If it was smaller,
    return a larger array with the original data in the center"""
    if arr.ndim != len(shape):
        raise Exception("Array and crop shape dimensions do not match")

    arr_shape = np.array(arr.shape)
    shape = np.array(shape)
    max_shape = np.stack([arr_shape, shape]).max(axis=0)
    output_arr = np.ones(max_shape, dtype=arr.dtype) * cval

    arr_min = ((max_shape - arr_shape) / 2).astype(np.int)
    arr_max = arr_min + arr_shape
    slicer_obj = tuple(slice(idx_min, idx_max, 1) for idx_min, idx_max in zip(arr_min, arr_max))
    output_arr[slicer_obj] = arr

    crop_min = ((max_shape - shape) / 2).astype(np.int)
    crop_max = crop_min + shape
    slicer_obj = tuple(slice(idx_min, idx_max, 1) for idx_min, idx_max in zip(crop_min, crop_max))
    return output_arr[slicer_obj].copy()  # Return a copy of the view, so the rest of memory can be GC


class VolumeDataGenerator(ImageDataGenerator):
    def __init__(self, *args, **kwargs):
        kwargs['data_format'] = 'channels_last'
        super().__init__(*args, **kwargs)

    def random_transform(self, x, seed=None):
        """Apply transformation to the x volume. Assuming axis are [Z, Y, X]"""
        x = np.moveaxis(x, 0, -1)  # volume axis are now [Y, X, Z]
        x = super().random_transform(x)  # Apply transformation on axial plane
        x = np.moveaxis(x, 0, -1)  # volume axis are now [X, Z, Y]
        x = super().random_transform(x)  # Apply transformation on coronal plane
        x = np.moveaxis(x, 0, -1)  # volume axis back to [Z, Y, X]
        return x

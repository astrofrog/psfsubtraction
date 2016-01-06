'''Functions that construct an iterable to iterate over regions.

These functions meant to be included into a `PSFFitter` object and thus they
all take the ``self`` argument.
The function should return an iterable, e.g. an iterator or a list of regions.
A "region" should be be a True/False index array of the same size as the
flattend (1-dimensional representation) image.
'''
from collections import defaultdict

import numpy as np


def image_at_once(self):
    '''Fit whole image at one.

    Returns
    -------
    regions: list
        List of one element (the image)
    '''
    return [np.ones_like(self.image1d, dtype=bool)]


def image_unmasked(self):
    '''Return the unmasked part of an image.

    Returns
    -------
    regions: list
        List of one element (the image)
    '''
    if hasattr(self.image, 'mask'):
        return [~np.ma.getmaskarray(self.image1d)]
    else:
        return image_at_once(self)


def mask_except_pixel(self, pix):
    '''Helper function - make True/False mask that is True at pix

    Parameters
    ----------
    pix : int
        Index in flattened image

    Returns
    -------
    m : np.array of bool
        Array that is True at and only at position ``pix``.
    '''
    m = self.dim2to1(np.zeros_like(self.image, dtype=bool))
    m[pix] = True
    return m


def pixel_by_pixel(self):
    '''Each pixel it its own region.

    This is an extreme LOCI variant, where each region is made up of a single
    pixel only.
    This function returns one region per unmasked image pixel.

    Note
    ----
    Even for images with just a few thousand pixels this method is
    too expensive in run time.

    Returns
    -------
    regions : iterator
        True/False index arrays
    '''
    # image_unmasked returns a list with one element.
    # All pixels to be used are marked True.
    mask = image_unmasked(self)[0]

    return imap(mask_except_pixel,
                ifilterfalse(lambda x: mask[x], range(len(mask))))


def group_by_basis(self):
    '''Group pixels with the same valid bases into one region.

    For each valid pixel in the image, this function checks which bases
    are valid at that pixel.
    It then groups pixels with the same valid bases into one region.

    If ``self.min_number_of_bases`` is set to an integer, only regions with
    at least that many valid bases are returned (default is 1).

    Theoretically, there could be 2^60 combinations of bases for 60 bases,
    but in practice the valid pixels in the bases are not randomly
    distributed, so that typically a much smaller number of regions is
    generated.

    Returns
    -------
    regions : list of index arrays
    '''
    imagemask = np.ma.getmaskarray(self.image1d)
    basemask = np.ma.getmaskarray(self.psfbase1d)

    min_bases = getattr(self, "min_number_of_bases", 1)

    D = defaultdict(list)
    for i in range(imagemask.shape[0]):
        # Add to the dict UNLESS the image itself is masked or TOO FEW bases
        # are valid
        if not imagemask[i] and ((~basemask[i, :]).sum() >= min_bases):
            D[tuple(basemask[i, :])].append(i)

    return D.values()

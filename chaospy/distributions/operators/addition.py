"""
Addition operator.

Example usage
-------------

Distribution and a constant::

    >>> distribution = chaospy.Normal(0, 1)+10
    >>> distribution
    Add(Normal(mu=0, sigma=1), 10)
    >>> distribution.sample(5).round(4)
    array([10.395 ,  8.7997, 11.6476,  9.9553, 11.1382])
    >>> distribution.fwd([9, 10, 11]).round(4)
    array([0.1587, 0.5   , 0.8413])
    >>> distribution.inv(distribution.fwd([9, 10, 11])).round(4)
    array([ 9., 10., 11.])
    >>> distribution.pdf([9, 10, 11]).round(4)
    array([0.242 , 0.3989, 0.242 ])
    >>> distribution.mom([1, 2, 3]).round(4)
    array([  10.,  101., 1030.])
    >>> distribution.ttr([1, 2, 3]).round(4)
    array([[10., 10., 10.],
           [ 1.,  2.,  3.]])

Construct joint addition distribution::

    >>> lhs = chaospy.Uniform(2, 3)
    >>> rhs = chaospy.Uniform(3, 4)
    >>> addition = lhs + rhs
    >>> addition
    Add(Uniform(lower=2, upper=3), Uniform(lower=3, upper=4))
    >>> joint1 = chaospy.J(lhs, addition)
    >>> joint2 = chaospy.J(rhs, addition)

Generate random samples::

    >>> joint1.sample(4).round(4)
    array([[2.2123, 2.0407, 2.3972, 2.2331],
           [6.0541, 5.2478, 6.1397, 5.6253]])
    >>> joint2.sample(4).round(4)
    array([[3.1823, 3.7435, 3.0696, 3.8853],
           [6.1349, 6.6747, 5.485 , 5.9143]])

Forward transformations::

    >>> lcorr = numpy.array([2.1, 2.5, 2.9])
    >>> rcorr = numpy.array([3.01, 3.5, 3.99])
    >>> joint1.fwd([lcorr, lcorr+rcorr]).round(4)
    array([[0.1 , 0.5 , 0.9 ],
           [0.01, 0.5 , 0.99]])
    >>> joint2.fwd([rcorr, lcorr+rcorr]).round(4)
    array([[0.01, 0.5 , 0.99],
           [0.1 , 0.5 , 0.9 ]])

Inverse transformations::

    >>> joint1.inv(joint1.fwd([lcorr, lcorr+rcorr])).round(4)
    array([[2.1 , 2.5 , 2.9 ],
           [5.11, 6.  , 6.89]])
    >>> joint2.inv(joint2.fwd([rcorr, lcorr+rcorr])).round(4)
    array([[3.01, 3.5 , 3.99],
           [5.11, 6.  , 6.89]])

Raw moments::

    >>> joint1.mom([(0, 1, 1), (1, 0, 1)]).round(4)
    array([ 6.    ,  2.5   , 15.0833])
    >>> joint2.mom([(0, 1, 1), (1, 0, 1)]).round(4)
    array([ 6.    ,  3.5   , 21.0833])
"""
from __future__ import division
from scipy.special import comb
import numpy
import chaospy

from ..baseclass import Distribution
from .operator import OperatorDistribution


class Add(OperatorDistribution):
    """Addition."""

    def __init__(self, left, right):
        super(Add, self).__init__(
            left=left,
            right=right,
            repr_args=[left, right],
        )

    def _lower(self, left, right, cache):
        """
        Distribution bounds.

        Example:
            >>> chaospy.Uniform().lower
            array([0.])
            >>> chaospy.Add(chaospy.Uniform(), 2).lower
            array([2.])
            >>> chaospy.Add(2, chaospy.Uniform()).lower
            array([2.])
        """
        if isinstance(left, Distribution):
            left = left._get_lower(cache=cache)
        if isinstance(right, Distribution):
            right = right._get_lower(cache=cache)
        return (left.T+right.T).T

    def _upper(self, left, right, cache):
        """
        Distribution bounds.

        Example:
            >>> chaospy.Uniform().upper
            array([1.])
            >>> chaospy.Add(chaospy.Uniform(), 2).upper
            array([3.])
            >>> chaospy.Add(2, chaospy.Uniform()).upper
            array([3.])

        """
        if isinstance(left, Distribution):
            left = left._get_upper(cache=cache)
        if isinstance(right, Distribution):
            right = right._get_upper(cache=cache)
        return (left.T+right.T).T

    def _cdf(self, xloc, left, right, cache):
        if isinstance(right, Distribution):
            left, right = right, left
        xloc = (xloc.T-numpy.asfarray(right).T).T
        uloc = left._get_fwd(xloc, cache=cache)
        return uloc

    def _pdf(self, xloc, left, right, cache):
        """
        Probability density function.

        Example:
            >>> print(chaospy.Uniform().pdf([-2, 0, 2, 4]))
            [0. 1. 0. 0.]
            >>> print(chaospy.Add(chaospy.Uniform(), 2).pdf([-2, 0, 2, 4]))
            [0. 0. 1. 0.]
            >>> print(chaospy.Add(2, chaospy.Uniform()).pdf([-2, 0, 2, 4]))
            [0. 0. 1. 0.]

        """
        if isinstance(right, Distribution):
            left, right = right, left
        xloc = (xloc.T-numpy.asfarray(right).T).T
        return left._get_pdf(xloc, cache=cache)

    def _ppf(self, uloc, left, right, cache):
        """
        Point percentile function.

        Example:
            >>> print(chaospy.Uniform().inv([0.1, 0.2, 0.9]))
            [0.1 0.2 0.9]
            >>> print(chaospy.Add(chaospy.Uniform(), 2).inv([0.1, 0.2, 0.9]))
            [2.1 2.2 2.9]
            >>> print(chaospy.Add(2, chaospy.Uniform()).inv([0.1, 0.2, 0.9]))
            [2.1 2.2 2.9]
        """
        if isinstance(right, Distribution):
            left, right = right, left
        xloc = left._get_inv(uloc, cache=cache)
        return (xloc.T+numpy.asfarray(right).T).T

    def _mom(self, keys, left, right, cache):
        """
        Statistical moments.

        Example:
            >>> print(numpy.around(chaospy.Uniform().mom([0, 1, 2, 3]), 4))
            [1.     0.5    0.3333 0.25  ]
            >>> print(numpy.around(chaospy.Add(chaospy.Uniform(), 2).mom([0, 1, 2, 3]), 4))
            [ 1.      2.5     6.3333 16.25  ]
            >>> print(numpy.around(chaospy.Add(2, chaospy.Uniform()).mom([0, 1, 2, 3]), 4))
            [ 1.      2.5     6.3333 16.25  ]
        """
        del cache
        keys_ = numpy.mgrid[tuple(slice(0, key+1, 1) for key in keys)]
        keys_ = keys_.reshape(len(self), -1)

        if isinstance(left, Distribution):
            if left.shares_dependencies(right):
                raise chaospy.StochasticallyDependentError(
                    "%s: left and right side of sum stochastically dependent." % self)
            left = [left._get_mom(key) for key in keys_.T]
        else:
            left = list(reversed(numpy.array(left).T**keys_.T))

        if isinstance(right, Distribution):
            right = [right._get_mom(key) for key in keys_.T]
        else:
            right = list(reversed(numpy.array(right).T**keys_.T))

        out = numpy.zeros(keys.shape)
        for idx in range(keys_.shape[1]):
            key = keys_.T[idx]
            coef = comb(keys.T, key)
            out += coef*left[idx]*right[idx]*(key <= keys.T)

        if numpy.asarray(out).shape:
            out = numpy.prod(out)
        return out

    def _ttr(self, kloc, left, right, cache):
        """
        Three terms recurrence coefficients.

        Example:
            >>> print(numpy.around(chaospy.Uniform().ttr([0, 1, 2, 3]), 4))
            [[ 0.5     0.5     0.5     0.5   ]
             [-0.      0.0833  0.0667  0.0643]]
            >>> print(numpy.around(chaospy.Add(chaospy.Uniform(), 2).ttr([0, 1, 2, 3]), 4))
            [[ 2.5     2.5     2.5     2.5   ]
             [-0.      0.0833  0.0667  0.0643]]
            >>> print(numpy.around(chaospy.Add(2, chaospy.Uniform()).ttr([0, 1, 2, 3]), 4))
            [[ 2.5     2.5     2.5     2.5   ]
             [-0.      0.0833  0.0667  0.0643]]

        """
        del cache
        if isinstance(right, Distribution):
            left, right = right, left
        coeff0, coeff1 = left._get_ttr(kloc)
        return coeff0+numpy.asarray(right), coeff1

    def _value(self, left, right, cache):
        del cache
        if isinstance(left, Distribution) or isinstance(right, Distribution):
            return self
        return left+right


def add(left, right):
    return Add(left, right)

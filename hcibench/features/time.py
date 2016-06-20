"""
Time-domain features.
"""

import numpy as np
from .base import Feature
from ..util import ensure_2d, rolling_window


class MAV(Feature):
    """Computes the mean absolute value of each signal.

    Mean absolute value is a popular feature for obtaining amplitude
    information from EMG, especially in gesture classification contexts.

    There is an optional windowing function applied to the rectified signal,
    described as MAV1 and MAV2 in some references (e.g. [2]).

    Parameters
    ----------
    weights : str or ndarray, optional
        Weights to use. Possible values:

            - 'mav' : all samples in the signal are weighted equally (default).
            - 'mav1' : rectangular window with the middle half of the signal
              receiving unit weight and the first and last quarters of the
              signal receiving half weight.
            - 'mav2' : similar to 'mav1', but weights on the first and last
              quarters increase and decrease between 0 and 1 respectively,
              forming a trapezoidal window.
            - [ndarray] : user-supplied weights to apply. Must be a 1D array
              with the same length as the signals received in the ``compute``
              method.

    References
    ----------
    .. [1] B. Hudgins, P. Parker, and R. N. Scott, "A New Strategy for
           Multifunction Myoelectric Control," IEEE Transactions on Biomedical
           Engineering, vol. 40, no. 1, pp. 82–94, 1993.
    .. [2] A. Phinyomark, P. Phukpattaranont, and C. Limsakul, "Feature
           Reduction and Selection for EMG Signal Classification," Expert
           Systems with Applications, vol. 39, no. 8, pp. 7420–7431, 2012.
    """

    def __init__(self, weights='mav'):
        self.weights = weights

        self._n = 0

    def compute(self, x):
        x = ensure_2d(x)

        n = x.shape[1]
        if n != self._n:
            self._n = n
            self._init_weights()

        return np.mean(self._w * np.absolute(x), axis=1)

    def _init_weights(self):
        if self.weights == 'mav':
            # unit weights
            self._w = np.ones(self._n)
        elif self.weights == 'mav1':
            # rectangular window de-emphasizing first and last quarters
            self._w = 0.5 * np.ones(self._n)
            self._w[int(0.25 * self._n):int(0.75 * self._n)] = 1
        elif self.weights == 'mav2':
            # trapezoidal window de-emphasizing first and last quarters
            self._w = np.ones(self._n)
            r1 = np.arange(0, int(0.25 * self._n))
            r2 = np.arange(int(0.75 * self._n), self._n)
            self._w[r1] = 4 * r1 / self._n
            self._w[r2] = 4 * (self._n - r2) / self._n
        elif isinstance(self.weights, np.ndarray):
            self._w = self.weights
            if len(self._w) != self._n:
                raise ValueError("Number of weights in custom window function "
                                 "does not match input size.")
        else:
            raise ValueError("Weights not recognized: should be 'mav', "
                             "'mav1', 'mav2', or a numpy array.")


class WL(Feature):
    """Computes the waveform length of each signal.

    Waveform length is the sum of the absolute value of the deltas between
    adjacent values (in time) of the signal.

    References
    ----------
    .. [1] B. Hudgins, P. Parker, and R. N. Scott, "A New Strategy for
           Multifunction Myoelectric Control," IEEE Transactions on Biomedical
           Engineering, vol. 40, no. 1, pp. 82–94, 1993.
    """

    def compute(self, x):
        x = ensure_2d(x)
        return np.sum(np.absolute(np.diff(x, axis=1)), axis=1)


class ZC(Feature):
    """Computes the number of zero crossings of each signal.

    A zero crossing occurs when two adjacent values (in time) of the signal
    have opposite sign.

    Parameters
    ----------
    threshold : float, optional
        A threshold for discriminating true zero crossings from those caused
        by low-level noise situated about zero. By default, no threshold is
        used, so every sign change in the signal is counted.

    References
    ----------
    .. [1] B. Hudgins, P. Parker, and R. N. Scott, "A New Strategy for
           Multifunction Myoelectric Control," IEEE Transactions on Biomedical
           Engineering, vol. 40, no. 1, pp. 82–94, 1993.
    """

    def __init__(self, threshold=0):
        self.threshold = threshold

    def compute(self, x):
        x = ensure_2d(x)
        # two conditions:
        #   1. sign changes from one sample to the next
        #   2. difference between adjacent samples bigger than threshold
        return np.sum(
            np.logical_and(
                np.diff(np.signbit(x), axis=1),
                np.absolute(np.diff(x, axis=1)) > self.threshold),
            axis=1)


class SSC(Feature):
    """Computes the number of slope sign changes of each signal.

    A slope sign change occurs when the middle value of a group of three
    adjacent values in the signal is either greater than or less than both of
    the other two.

    Parameters
    ----------
    threshold : float, optional
        A threshold for discriminating true slope sign changes from those
        caused by low-level noise fluctuating about a specific value. By
        default, no threshold is used, so every slope sign change in the signal
        is counted.

    References
    ----------
    .. [1] B. Hudgins, P. Parker, and R. N. Scott, "A New Strategy for
           Multifunction Myoelectric Control," IEEE Transactions on Biomedical
           Engineering, vol. 40, no. 1, pp. 82–94, 1993.
    """

    def __init__(self, threshold=0):
        self.threshold = threshold

    def compute(self, x):
        x = ensure_2d(x)
        # two conditions:
        #   1. sign of the diff changes from one pair of samples to the next
        #   2. the max of two adjacent diffs is bigger than threshold
        return np.sum(
            np.logical_and(
                np.diff(np.signbit(np.diff(x, axis=1)), axis=1),
                np.max(rolling_window(
                    np.absolute(
                        np.diff(x, axis=1)), 2), axis=-1) > self.threshold),
            axis=1)

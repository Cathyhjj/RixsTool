#/*##########################################################################
# Copyright (C) 2004-2013 European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF by the Software group.
#
# This toolkit is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# PyMca is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# PyMca; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# PyMca follows the dual licensing model of Riverbank's PyQt and cannot be
# used as a free plugin for a non-free program.
#
# Please contact the ESRF industrial unit (industry@esrf.fr) if this license
# is a problem for you.
#############################################################################*/
__author__ = "Tonn Rueter - ESRF Data Analysis Unit"

import numpy

# Numeric routines from PyMca
from PyMca5.PyMcaMath.fitting.Gefit import LeastSquaresFit as LSF
from PyMca5.PyMcaMath.fitting import SpecfitFunctions as SF
from PyMca5.PyMcaMath.fitting.SpecfitFuns import gauss as gaussianModel
from PyMca5.PyMcaMath import SNIPModule as SNIP

# IO and Datahandling from RixsTool
from RixsTool.Project import RixsProject
from RixsTool.Items import FunctionItem
from RixsTool.Functions import Fit

DEBUG = 0


class ImageOp(object):
    def __init__(self):
        object.__init__(self)
        self._ops = {}


class Filter(ImageOp):
    def __init__(self):
        ImageOp.__init__(self)
        self._ops = {
            'bandpass': self.bandPassFilter
        }

    #def bandPassFilter(self, image, params):
    @staticmethod
    def bandPassFilter(image, params):
        """
        :param ndarray image: Two dimensional numpy.ndarray
        :param dict params: Contains parameters low, high and offset

        General purpose bandpass filter. Possible parameters are

        low
            lower threshold (default: minimum value)

        high
            upper threshold (default: maximum value)

        offset
            baseline (default: 0)
        replace
            value to be used as replacement (default: minimum value)

        The offset is subtracted from the image. Values above the upper threshold or
        below the lower threshold are replaced by a given replacement value. *Notice:* the image will be casted
        into the type of offset.

        :returns ndarray: Filtered image
        """
        imMin = image.min()
        imMax = image.max()
        lo = params.get('low', imMin)
        hi = params.get('high', imMax)
        offset = params.get('offset', 0.)
        replace = params.get('replace', 0.)

        if DEBUG >= 1:
            print('Filter.bandPassFilter -- calculating..')
            print('\thi = %s (type: %s)' % (str(hi), str(type(hi))))
            print('\tlo = %s (type: %s)' % (str(lo), str(type(lo))))
            print('\toffset = %s (type: %s)' % (str(offset), str(type(offset))))
            print('\treplace = %s (type: %s)' % (str(replace), str(type(replace))))

        out = image.astype(type(offset)) - offset
        out = numpy.where((lo <= out), out, replace)
        out = numpy.where((out <= hi), out, replace)

        if DEBUG >= 1:
            print('\timage.min = %s (type: %s)' % (str(image.min()), str(type(image.min()))))
            print('\timage.max = %s (type: %s)' % (str(image.max()), str(type(image.max()))))
            print('\tout.min = %s (type: %s)' % (str(out.min()), str(type(out.min()))))
            print('\tout.max = %s (type: %s)' % (str(out.max()), str(type(out.max()))))

        return out

    @staticmethod
    def bandPassFilterID32(image, params):
        """
        :param ndarray image: Two dimensional numpy.ndarray
        :param dict params: Contains parameters specific to the ID32 detector (c.f. comments in source code)

        The method implements a bandpass filter specific to the measurement configuration of
        beamline ID32 at the ESRF.

        :returns ndarray: Filtered image
        """
        #
        # -- THRESHOLDING --
        # The values for upper and lower thresholds depend on certain characteristics of
        # the detector. The detector efficiency is a function of the photon energy and
        # the number of electrons induced by a single photon.
        #
        # binning: Hardware binning in the detector, 4 in the example
        # photon energy: guess what..
        #
        photonEnery = params.get('energy', 931.942)  # From header...
        binning = params.get('binning', 4)

        detectorEfficiency = photonEnery * 0.24801587301587297  # 1. / (3.6 * 1.12) = 0.248...
        lower = detectorEfficiency * 0.035  # TODO: Where does 0.035 come from?!
        upper = detectorEfficiency * binning * 0.9

        #
        # -- BASELINE --
        # Values beneath the baseline are cut off. The baseline is derived from the image
        # itself, by taking the mean of a dark part of the image (here: the first 100 rows)
        #
        # exposureTime: time to record an entire image in seconds
        # DC: counts per pixel per second
        #
        exposureTime = params.get('preset', 300)
        dc = params.get('dc', 0.00016)

        offset = numpy.mean(image[:100, :]) + 1
        baseline = offset + exposureTime * dc

        parameters = {
            'offset': baseline,
            'low': lower,
            'high': upper,
            'replace': 0
        }

        if DEBUG >= 1:
            print('Filter.bandPassFilterID32 -- values:')
            for key, value in parameters.items():
                print('\t%s = %s (type: %s)' % (str(key), str(value), str(type(value))))

        #print('Filter.bandPassFilterID32 -- parameters:\n\t%s' % str(parameters))
        return Filter.bandPassFilter(image, parameters)


class Alignment(ImageOp):
    def __init__(self=None):
        ImageOp.__init__(self)
        self._ops = {
            'maxAlignment': self.maxAlignment,
            'fftAlignment': self.fftAlignment,
            'centerOfMassAlignment': self.centerOfMassAlignment
        }

    @staticmethod
    def maxAlignment(image, params):
        # TODO: Add normalization flag
        idx0 = params.get('idx0', 0)
        axis = params.get('axis', -1) # Axis defines direction of curves
        scale = params.get('scale', None)

        if axis < 0:
            rows, cols = image.shape
            if rows < cols:
                axis = 0
            else:
                axis = 1

        if axis == 0:
            nCurves, nPoints = image.shape
            curves = image
        elif axis == 1:
            nPoints, nCurves = image.shape
            curves = image.T
        else:
            raise ValueError('Alignment instance -- Axis must be either -1, 0 or 1')

        shiftList = [float('NaN')] * nCurves

        pos0 = curves[idx0].argmax()

        for idx, y in enumerate(curves):
            shift = pos0 - y.argmax()
            shiftList[idx] = shift

        shiftArray = numpy.asarray(shiftList)
        if scale:
            shiftArray *= numpy.average(numpy.diff(scale))

        #ddict = {
        #    'op': 'maxAlignment',
        #    'shiftList': shiftArray
        #}
        #return ddict
        return shiftArray

    @staticmethod
    def centerOfMassAlignment(image, params):
        idx0 = params.get('idx0', 0)
        axis = params.get('axis', -1) # Axis defines direction of curves
        portion = params.get('portion', .80)
        scale = params.get('scale', None)

        # Determine which axis defines curves
        if axis < 0:
            # If axis not specified..
            rows, cols = image.shape
            # ..align along smaller axis
            if rows < cols:
                axis = 0
            else:
                axis = 1

        if axis == 0:
            nCurves, nPoints = image.shape
            curves = image
        elif axis == 1:
            nPoints, nCurves = image.shape
            curves = image.T
        else:
            raise ValueError('Alignment instance -- Axis must be either -1, 0 or 1')

        shiftList = nCurves * [float('NaN')]

        y0 = curves[idx0]
        pos0 = y0.argmax()
        ymin0, ymax0 = y0.min(), y0.max()
        normFactor = ymax0-ymin0
        if float(normFactor) <= 0.:
            # Curve is constant
            raise ZeroDivisionError('Alignment.centerOfMass -- Trying to align on constant curve')
        ynormed0 = (y0-ymin0)/normFactor

        threshold = portion * float(ynormed0[pos0])
        left, right = pos0, pos0
        while  ynormed0[left] > threshold:
            left -= 1
        while  ynormed0[right] > threshold:
            right += 1
        if left < 0 or right >= nPoints:
            raise IndexError('Alignment.centerOfMassAlignment: 0-th index out of range (left: %d, right: %d)'%(left, right))
        mask = numpy.arange(left, right+1, dtype=int)
        pos0 = numpy.trapz(ynormed0[mask] * mask) / numpy.trapz(ynormed0[mask])

        for idx, y in enumerate(curves):
            # Normalize betw. zero an one
            ymin, ymax = y.min(), y.max()
            normFactor = ymax-ymin
            if float(normFactor) <= 0.:
                # Curve is constant
                continue
            ynormed = (y-ymin)/normFactor

            idxMax = ynormed.argmax()
            left, right = idxMax, idxMax
            while ynormed[left] > threshold:
                left -= 1
            while ynormed[right] > threshold:
                right += 1
            if left < 0 or right >= nPoints:
                raise IndexError('Alignment.centerOfMassAlignment: index out of range (left: %d, right: %d)'%(left, right))
            mask = numpy.arange(left, right+1, dtype=int)
            if DEBUG >= 1:
                print('mask:', mask)
            shift = pos0 - numpy.trapz(ynormed[mask] * mask) / numpy.trapz(ynormed[mask])
            if DEBUG >= 1:
                print('\t%d\t%f'%(idx, shift))
            shiftList[idx] = shift

        shiftArray = numpy.asarray(shiftList)
        if scale:
            shiftArray *= numpy.average(numpy.diff(scale))
        #ddict = {
        #    'op': 'centerOfMassAlignment',
        #    'shiftList': shiftArray
        #}
        #return ddict
        return shiftArray

    @staticmethod
    def fftAlignment(image, params):
        idx0 = params.get('idx0', 0)
        axis = params.get('axis', -1)  # Axis defines direction of curves
        portion = params.get('portion', .80)
        minChannel = params.get('minChannel', 0)
        maxChannel = params.get('maxChannel', -1)
        scale = params.get('scale', None)

        # Determine which axis defines curves
        if axis < 0:
            # If axis not specified..
            rows, cols = image.shape
            # ..align along smaller axis
            if rows < cols:
                axis = 0
            else:
                axis = 1

        if axis == 0:
            nCurves, nPoints = image.shape
            curves = image
        elif axis == 1:
            nPoints, nCurves = image.shape
            curves = image.T
        else:
            raise ValueError('Alignment instance -- Axis must be either -1, 0 or 1')

        # Determine, if a window is defined
        if maxChannel < 0:
            maxChannel = nPoints - 1
        window = numpy.arange(
            start=minChannel,
            stop=maxChannel,
            step=1,
            dtype=numpy.uint16
        )
        #print('fftAlignment -- window: %s' % str(window))
        if DEBUG >= 1:
            print('fftAlignment -- window.shape: %s' % str(window.shape))

        shiftList = nCurves * [float('NaN')]

        #y0 = curves[idx0]
        y0 = curves[idx0][window]
        if DEBUG >= 1:
            print('fftAlignment -- y0.shape: %s' % str(y0.shape))
        fft0 = numpy.fft.fft(y0)

        for idx, y in enumerate(curves):
            if DEBUG >= 1:
                print('fftAlignment -- y.shape: %s' % str(y.shape))
            data = y[window]
            if DEBUG >= 1:
                print('fftAlignment -- data.shape: %s' % str(data.shape))
            ffty = numpy.fft.fft(data)
            #ffty = numpy.fft.fft(y)
            shiftTmp = numpy.fft.ifft(fft0 * ffty.conjugate()).real
            shiftPhase = numpy.zeros(shiftTmp.shape, dtype=shiftTmp.dtype)
            m = shiftTmp.size//2
            shiftPhase[m:] = shiftTmp[:-m]
            shiftPhase[:m] = shiftTmp[-m:]

            # Normalize shiftPhase between 0 and 1 to standardize thresholding
            shiftPhaseMin = shiftPhase.min()
            shiftPhaseMax = shiftPhase.max()
            normFactor = shiftPhaseMax - shiftPhaseMin
            if float(normFactor) <= 0.:
                if DEBUG >= 1:
                    print('fftAlignment -- normFactor is zero')
                continue
            if DEBUG >= 1:
                print('fftAlignment -- \n\t\t\tshiftPhaseMin: %f\n\t\t\tshiftPhaseMax: %f' % (shiftPhaseMin, shiftPhaseMax))
            shiftPhase = (shiftPhase-shiftPhaseMin)/normFactor

            # Thresholding: The noisier the data is, the more likely it is for the
            # normalization to be ineffective, i.e. the whole range of shiftPhase
            # is used later on.
            idxMax = shiftPhase.argmax()
            left, right = idxMax, idxMax
            threshold = portion
            while shiftPhase[left] >= threshold:
                if left <= 0:
                    if DEBUG >= 1:
                        print('fftAlignment -- reached left limit')
                    left = 0
                    break
                left -= 1
            while shiftPhase[right] >= threshold:
                if right >= len(shiftPhase)-1:
                    if DEBUG >= 1:
                        print('fftAlignment -- reached right limit')
                    right = len(shiftPhase)-1
                    break
                right += 1

            mask = numpy.arange(left, right+1, 1, dtype=numpy.uint16)
            if DEBUG >= 1:
                print('fftAlignment -- mask: %s' % str(mask))
            # The shift is determined by center-of-mass around idxMax
            shiftTmp = numpy.sum((shiftPhase[mask] * mask/shiftPhase[mask].sum()))
            #shift = (shiftTmp - m) * (x[1] - x[0])
            # x-range is pixel count..
            shift = (shiftTmp - m)
            shiftList[idx] = shift
            if DEBUG >= 1:
                print('fftAlignment -- shiftList[%d]: %s' % (idx, str(shift)))

        #ddict = {
        #    'op': 'fftAlignment',
        #    'shiftList': shiftList
        #}
        #return ddict
        #return shiftList
        return numpy.ascontiguousarray(shiftList)

    @staticmethod
    def fitAlignment(image, params):
        idx0 = params.get('idx0', 0)
        axis = params.get('axis', -1)  # Axis defines direction of curves
        snipWidth = params.get('snipWidth', None)
        peakSearch = params.get('peakSearch', False)

        #
        # Determine which axis defines curves
        # Make shure to convert image to float!!!
        #
        if axis < 0:
            # If axis not specified..
            rows, cols = image.shape
            # ..align along smaller axis
            if rows < cols:
                axis = 0
            else:
                axis = 1

        if axis == 0:
            nCurves, nPoints = image.shape
            curves = numpy.float64(image)
        elif axis == 1:
            nPoints, nCurves = image.shape
            curves = numpy.float64(image.T)
        else:
            raise ValueError('Alignment instance -- Axis must be either -1, 0 or 1')

        #
        # Image preprocessing: Snip background
        #
        imRows, imCols = image.shape
        if snipWidth is None:
            snipWidth = max(imRows, imCols)//10
        specfitObj = SF.SpecfitFunctions()

        background = numpy.zeros(shape=curves.shape,
                                 dtype=numpy.float64)
        for idx, curve in enumerate(curves):
            background[idx] = SNIP.getSnip1DBackground(curve, snipWidth)
        subtracted = curves-background
        normResult = Normalization.zeroToOne(image=subtracted,
                                             params={})
        normalized = normResult['image']

        #
        # Loop through curves: Find peak (max..), Estimate fit params, Perform Gaussian fit
        #
        fitList = nCurves * [float('NaN')]
        if DEBUG >= 1:
            print('Alignment.fitAlignment -- fitting..')
        for idx, y in enumerate(subtracted):
            #
            # Peak search
            #
            if peakSearch:
                try:
                    # Calculate array with all peak indices
                    peakIdx = numpy.asarray(specfitObj.seek(y, yscaling=100.),
                                            dtype=int)
                    # Extract highest feature
                    maxIdx = y[peakIdx].argsort()[-1]
                except IndexError:
                    if DEBUG >= 1:
                        print('Alignment.fitAlignment -- No peaks found..')
                    return None
                except SystemError:
                    if DEBUG >= 1:
                        print('Alignment.fitAlignment -- Peak search failed. Continue with y maximum')
                    peakIdx = [y.argmax()]
                    maxIdx = 0
            else:
                peakIdx = [y.argmax()]
                maxIdx = 0
            height = float(y[peakIdx][maxIdx]) + curves[idx].min()
            pos = float(peakIdx[maxIdx])

            #
            # Estimate FWHM
            #
            fwhmIdx = numpy.nonzero(y >= .5*normalized[idx])[0]
            # Underestimates FWHM, since carried out on normalized image
            fwhm = float(fwhmIdx.max()-fwhmIdx.min())

            #
            # Peak fit: Uses actual data
            #
            #xrange = numpy.arange(0, len(y), dtype=y.dtype) # Full range
            mask = numpy.nonzero(y >= .1*normalized[idx])[0]
            ydata = curves[idx,mask]
            #ydata -= ydata.min()
            try:
                fitp, chisq, sigma = LSF(gaussianModel,
                                         numpy.asarray([height, pos, fwhm]),
                                         xdata=mask,
                                         ydata=(ydata-ydata.min()))
                if DEBUG >= 1:
                    print('\tCurve %d -- fitp: %s' % (idx, str(fitp)))
                    print('\tCurve %d -- chisq: %s' % (idx, str(chisq)))
                    print('\tCurve %d -- sigma: %s' % (idx, str(sigma)))
            except numpy.linalg.linalg.LinAlgError:
                fitp, chisq, sigma = [None, None, None],\
                                     float('Nan'),\
                                     float('Nan')
                if DEBUG >= 1:
                    print('\tCurve %d -- Fit failed!' % idx)
            fitList[idx] = fitp # ftip is 3-tuple..

        posIdx = 1  # ..2nd argument of fitp is peak position
        shift0 = fitList[idx0][posIdx]
        shiftList = [shift0-fit[posIdx] for fit in fitList]

        #ddict = {
        #    'op': 'fitAlignment',
        #    'shiftList': shiftList
        #}
        #return ddict
        return shiftList


class Interpolation(ImageOp):
    def __init__(self=None):
        ImageOp.__init__(self)
        self._ops = {
            'axisInterpolation': self.axisInterpolation
        }

    def axisInterpolation(self, image, params):
        axis = params.get('axis', -1)
        if axis < 0:
            # If axis not specified..
            rows, cols = image.shape
            # ..sum along larger axis
            if rows < cols:
                axis = 1
            else:
                axis = 0
        ddict = {}
        if DEBUG >= 1:
            print('Interpolation.axisInterpolation -- not implemented')
        return ddict


class Integration(ImageOp):
    def __init__(self=None):
        ImageOp.__init__(self)
        self._ops = {
            'axisSum': self.axisSum,
            'sliceAndSum': self.sliceAndSum
        }

    @staticmethod
    def axisSum(image, params):
        axis = params.get('axis', -1)
        if axis < 0:
            # If axis not specified..
            rows, cols = image.shape
            # ..sum along smaller axis
            if rows < cols:
                axis = 0
            else:
                axis = 1
        return numpy.sum(image, axis=axis)

    @staticmethod
    def sliceAndSum(image, params):
        sumAxis = params.get('sumAxis', 1)
        sliceAxis = params.get('sliceAxis', 1)
        params['axis'] = sliceAxis
        slices = Manipulation.slice(image, params)
        #result = [slice_.sum(axis=sumAxis) for slice_ in slices]

        nRows, nCols = image.shape
        if sliceAxis == 1:
            # Slice along columns
            result = numpy.zeros((nRows, len(slices)), dtype=image.dtype)
        else:
            # Slice along rows
            result = numpy.zeros((len(slices), nCols), dtype=image.dtype)
        for idx, slice_ in enumerate(slices):
            if sliceAxis == 1:
                result[:, idx] = slice_.sum(axis=sumAxis)
            else:
                result[idx, :] = slice_.sum(axis=sumAxis)
        #result = numpy.asarray([slice_.sum(axis=sumAxis) for slice_ in slices], dtype=image.dtype)
        #ddict = {
        #    'op': 'sliceAndSum',
        #    'summedSlices': result
        #}
        #return ddict
        if DEBUG >= 1:
            print('Integration.sliceAndSum -- result.shape: %s' % str(result.shape))
        return result


class Normalization(ImageOp):
    def __init__(self=None):
        ImageOp.__init__(self)
        self._ops = {
            'zeroToOne': self.zeroToOne
        }

    @staticmethod
    def zeroToOne(image, params):
        offset  = image.min()
        maximum = image.max()
        normFactor = maximum - offset

        if DEBUG >= 1:
            print('zeroToOne, before -- min: %.3f, max: %.3f'%(offset, maximum))

        if normFactor == 0.:
            normalized = numpy.zeros(shape=image.shape,
                                     dtype=image.dtype)
        else:
            normalized = (image - offset)/normFactor
        if DEBUG >= 1:
            print('zeroToOne, after  -- min: %.3f, max: %.3f' % (normalized.min(), normalized.max()))
        ddict = {
            'op': 'zeroToOne',
            'image': normalized
        }
        return ddict


class Manipulation(ImageOp):
    def __init__(self):
        ImageOp.__init__(self)
        self._ops = {
            'slice': self.slice
        }

    @staticmethod
    def skewAlongAxis(image, params):
        nRows, nCols = image.shape

        axis = params.get('foobar', None)
        # if axis is specified, skew along longer axis
        # i.e. loop along shorter axis
        if axis is None:
            if nRows > nCols:
                axis = 1
                longAxis = 0
                shortAxis = 1
            else:
                longAxis = 1
                shortAxis = 0

        shiftArray = params.get('shiftArray', None)
        if shiftArray is None:
            raise ValueError('Manipulation.skewAlongAxis -- must provide shiftArray')
        if not isinstance(shiftArray, numpy.ndarray):
            shiftArray = numpy.ascontiguousarray(shiftArray)

        oversampling = params.get('oversampling', 1)
        if shortAxis == 0:
            resultShape = (nRows, oversampling * nCols)
        else:
            resultShape = (oversampling * nRows, nCols)
        result = numpy.zeros(resultShape)
        interpRange = numpy.linspace(0, 2047, result.shape[longAxis])
        if shortAxis == 0:
            points = numpy.arange(0, image.shape[1], 1, dtype=numpy.uint16)
        else:
            points = numpy.arange(0, image.shape[0], 1, dtype=numpy.uint16)

        #print(shortAxis)
        #print(longAxis)
        #print(image.shape)
        #print(result.shape)
        #print(len(interpRange))
        #print(len(points))

        for idx in range(image.shape[shortAxis]):
            if shortAxis == 0:
                vector = image[idx, :]
            else:
                vector = image[:, idx]
            shift = shiftArray[idx]

            #
            # Perform interpolation. Values outside the function range are set to not-a-number values
            #
            interpolated = numpy.interp(
                x=interpRange-shift,
                xp=points,
                fp=vector,
                right=float('NaN'),
                left=float('NaN')
            )
            interpolated /= float(oversampling)

            #
            # Remove not-a-number values
            #
            if numpy.any(numpy.isfinite(interpolated)):
                interpolated = numpy.nan_to_num(interpolated)

            if shortAxis == 0:
                result[idx, :] = interpolated
            else:
                result[:, idx] = interpolated

        return result

    @staticmethod
    def slice(image, params):
        binWidth = params.get('binWidth', 8)
        axis = params.get('axis', 1)
        mode = params.get('mode', 'strict')
        if axis:
            size = (image.shape[0], binWidth)
        else:
            size = (binWidth, image.shape[1])
        lim = image.shape[axis]
        if mode not in ['strict']:  # TODO: implement mode that puts surplus cols rows as last element in tmpList
            raise ValueError('Integration.binning: Unknown mode %s' % mode)
        if lim % binWidth and mode == 'relaxed':
            raise Warning('Binning neglects curves at the end')
        numberOfBins = lim//binWidth
        tmpList = numberOfBins*[numpy.zeros(size, dtype=image.dtype)]
        for idx in range(numberOfBins):
            lower = idx * binWidth
            upper = lower + binWidth
            if upper > lim:
                break
            if axis:
                # Slice along cols (axis==1)
                tmpList[idx] = numpy.copy(image[:, lower:upper])
            else:
                # Slice along rows (axis==0)
                tmpList[idx] = numpy.copy(image[lower:upper, :])
            if DEBUG >= 1:
                print('Manipulation.slice -- tmpList[%d].shape: %s' % (idx, str(tmpList[idx].shape)))

        return tmpList


class SlopeCorrection(object):
    __doc__ = """ImageOp class to determine and apply slope correction to images as recorded on ID32"""

    def __init__(self):
        self.smileFunction = None

    @staticmethod
    def alignImage(image, smileFunction):
        """
        :param ndarray image: Uncorrected RIXS image
        :param FunctionItem smileFunction: smile function

        Applies
        """
        # Larger axis is shiftAxis, small is sumAxis
        nRows, nCols = image.shape
        if nRows > nCols:
            shiftAxis = 0  # ..rows
        else:
            shiftAxis = 1  # ..cols
        sumLength = min(nRows, nCols)
        #
        # Apply the quadratic
        #
        shiftPerColumn = smileFunction.sample(numpy.arange(sumLength))

        corrected = Manipulation.skewAlongAxis(
            image=image,
            params={
                'axis': shiftAxis,
                'oversampling': 2,
                'shiftArray': shiftPerColumn
            }
        )

        return corrected

    @staticmethod
    def slopeCorrection(image, binWidth, window=None):
        """
        :param ndarray image: Two dimensional numpy array
        :param int binWidth: Number of columns or rows to be summed up to for a slice
        :param tuple window: 2-tuple containing minIdx and maxIdx, i.e. the minimum and the maximum index between which
         data points of each slice are used to calculate the shift between the slices

        :returns FunctionItem smileFunction: Quadtratic fit of the shift over the number of rows/columns (and *not* the
         number of slices!)

        :raises numpy.RankWarning: In case the least squares fit is badly conditioned.
        :raises IndexError: If the window is ill-defined (i.e. minIdx > maxIdx)
        """
        # Larger axis is shiftAxis, small is sumAxis
        nRows, nCols = image.shape
        if nRows > nCols:
            sumAxis = 1  # ..cols
        else:
            sumAxis = 0  # ..rows

        #
        # Slice the image by a given binning
        #
        sliceParams = {
            'sumAxis': sumAxis,
            'binWidth': binWidth
        }
        sliced = Integration.sliceAndSum(image, sliceParams)
        #print('SlopeCorrection.slopeCorrection -- sliced.shape: %s' % str(sliced.shape))

        #
        # Calculate the inter-column shift using FFT cross correlation alignment
        #
        if window:
            minIdx, maxIdx = window
        else:
            minIdx, maxIdx = 0, max(nRows, nCols)
        if minIdx > maxIdx:
            raise IndexError('SlopeCorrection.slopeCorrection -- ill-defined window: %s' % str(window))

        alignParams = {
            'idx0': 0,
            'minChannel': minIdx,
            'maxChannel': maxIdx
        }
        shifts = Alignment.fftAlignment(sliced, alignParams)

        #
        # Fit a quadratic function to the shifts. poly is of type AnalyticItem
        #
        fitRange = binWidth//2 + numpy.arange(len(shifts)) * binWidth
        smileFunction = Fit.quadratic(
            fitvalues=shifts,
            x=fitRange,
            key='Slope correction'
        )

        return smileFunction


def run_test():

    from matplotlib import pyplot as plt

    directory = '/home/truter/lab/mock_folder/Images'
    project = RixsProject()
    project.crawl(directory)

    carbonTape = project['LBCO0483.edf'].item()
    #filtered = Filter.bandPassFilterID32(carbonTape.array, {})
    filtered = Filter.bandPassFilter(carbonTape.array, {
        'offset': 114,
        'low': 8,
        'high': 803
    })

    plt.plot(filtered.sum(axis=1))
    #plt.plot(carbonTape.array.sum(axis=1))
    plt.show()

    return

    itemList = [child.item() for child in project['Images'].children]
    filteredList = [Filter.bandPassFilterID32(item.array, {}) for item in itemList]
    #polyList = [SlopeCorrection.slopeCorrection(arr, 64) for arr in filteredList]
    polyList = [SlopeCorrection.slopeCorrection(im, 128) for im in filteredList]
    corretedList = [SlopeCorrection.alignImage(im, func) for im, func in zip(filteredList, polyList)]

    '''
    a = [float('Nan')] * len(polyList)
    b = [float('Nan')] * len(polyList)
    c = [float('Nan')] * len(polyList)
    for idx, poly in enumerate(polyList):
        par = poly.parameters
        a[idx] = par['a']
        b[idx] = par['b']
        c[idx] = par['c']
    '''

    f = open('/home/truter/lab/rixs_own/all.dat', 'w')
    for idx, (item, im) in enumerate(zip(itemList, corretedList)):
        summed = im.sum(axis=1)[::-1]
        points = numpy.arange(len(summed))

        f.write('#S %d\n' % idx)
        f.write('#N 1\n')

        f.write('#L col0  %s\n' % item.key())
        #numpy.vstack((summed, points)).tofile(f, sep='\n')
        summed.tofile(f, sep='\n')
        f.write('\n\n')
    f.close()
    return

    #poly0 = SlopeCorrection.slopeCorrection(filtered, 16, (940, 1030))

    poly = FunctionItem('', '')
    expression = lambda x, a, b, c: a * x**2 + b * x + c
    parameters = {
        'a': -5.25213*10**-5,
        'b': 0.18877,
        'c': 0.
    }
    poly.setExpression(expression)
    poly.setParameters(parameters)

    #poly0 = SlopeCorrection.slopeCorrection(filtered, 128)
    carbonTapeCorrected = SlopeCorrection.alignImage(filtered, poly)
    sum0 = carbonTapeCorrected.sum(axis=1)[::-1]
    carbonOut = open('/home/truter/lab/rixs_own/own0482.dat', 'w')
    (sum0-sum0.min()).tofile(carbonOut, sep='\n')

    plt.plot(sum0)
    plt.show()

    return
    firstResonant = project['LBCO0483.edf'].item()
    filtered_imf = Filter.bandPassFilterID32(firstResonant.array, {})
    poly = SlopeCorrection.slopeCorrection(filtered_imf, 64, (930, 1040))

    firstCorrected = SlopeCorrection.alignImage(filtered, poly)
    sumCarbon = firstCorrected.sum(axis=1)[::-1]
    carbonOut = open('/home/truter/lab/rixs_own/own0482_CuCalib.dat', 'w')
    (sumCarbon-sumCarbon.min()).tofile(carbonOut, sep='\n')

    poly1 = SlopeCorrection.slopeCorrection(filtered, 16, (930, 1040))
    poly2 = SlopeCorrection.slopeCorrection(filtered, 32, (930, 1040))
    poly3 = SlopeCorrection.slopeCorrection(filtered, 64, (930, 1040))
    poly4 = SlopeCorrection.slopeCorrection(filtered, 128, (930, 1040))
    poly5 = SlopeCorrection.slopeCorrection(filtered, 256, (930, 1040))
    corrected1 = SlopeCorrection.alignImage(filtered_imf, poly1)
    corrected2 = SlopeCorrection.alignImage(filtered_imf, poly2)
    corrected3 = SlopeCorrection.alignImage(filtered_imf, poly3)
    corrected4 = SlopeCorrection.alignImage(filtered_imf, poly4)
    corrected5 = SlopeCorrection.alignImage(filtered_imf, poly5)
    sum1 = corrected1.sum(axis=1)[::-1]
    sum2 = corrected2.sum(axis=1)[::-1]
    sum3 = corrected3.sum(axis=1)[::-1]
    sum4 = corrected4.sum(axis=1)[::-1]
    sum5 = corrected5.sum(axis=1)[::-1]
    firstResonantOut1 = open('/home/truter/lab/rixs_own/own0483_16.dat', 'w')
    firstResonantOut2 = open('/home/truter/lab/rixs_own/own0483_32.dat', 'w')
    firstResonantOut3 = open('/home/truter/lab/rixs_own/own0483_64.dat', 'w')
    firstResonantOut4 = open('/home/truter/lab/rixs_own/own0483_128.dat', 'w')
    firstResonantOut5 = open('/home/truter/lab/rixs_own/own0483_256.dat', 'w')

    #plt.plot(sum0-sum0.min())
    plt.plot(sum1-sum1.min(), label='poly1')
    plt.plot(sum2-sum2.min(), label='poly2')
    plt.plot(sum3-sum3.min(), label='poly3')
    plt.plot(sum4-sum4.min(), label='poly4')
    plt.plot(sum5-sum5.min(), label='poly5')
    plt.legend()
    plt.show()

    #(sum0-sum0.min()).tofile(carbonOut, sep='\n')
    (sum1-sum1.min()).tofile(firstResonantOut1, sep='\n')
    (sum2-sum2.min()).tofile(firstResonantOut2, sep='\n')
    (sum3-sum3.min()).tofile(firstResonantOut3, sep='\n')
    (sum4-sum4.min()).tofile(firstResonantOut4, sep='\n')
    (sum5-sum5.min()).tofile(firstResonantOut5, sep='\n')


if __name__ == '__main__':
    run_test()
    print('io.run_test -- Done')

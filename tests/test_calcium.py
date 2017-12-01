from neuroglia.calcium import MedianFilterDetrender, SavGolFilterDetrender
from neuroglia.calcium import CalciumDeconvolver
from oasis.functions import gen_data
from sklearn.base import clone

import numpy as np
import pandas as pd
import xarray as xr

import numpy.testing as npt
import xarray.testing as xrt


# Test functions perform as expected
true_b = 2
y, true_c, true_s = map(np.squeeze, gen_data(N=3, b=true_b, seed=0))
y = y.T
TIME = np.arange(0, len(y)/30, 1/30.)
LBL = ['a', 'b', 'c']
sin_scale = 5

# data = y
DFF = pd.DataFrame(y, TIME, LBL)
DFF_WITH_DRIFT = DFF.apply(lambda y: y + sin_scale*np.sin(.05*TIME),axis=0)

assert np.all(np.mean(DFF) > 2)

def test_MedianFilterDetrender():
    detrender = MedianFilterDetrender()
    tmp = detrender.fit_transform(DFF_WITH_DRIFT)
    assert np.all(np.isclose(np.mean(tmp), 0, atol=.1))
    clone(detrender)

def test_SavGolFilterDetrender():
    detrender = SavGolFilterDetrender()
    tmp = detrender.fit_transform(DFF_WITH_DRIFT)
    assert np.all(np.isclose(np.mean(tmp), 0, atol=.1))
    clone(detrender)

def test_CalciumDeconvolver():
    deconvolver = CalciumDeconvolver()
    tmp = deconvolver.fit_transform(DFF)
    assert np.all(np.array([np.corrcoef(true_s[n], np.array(tmp[a]))[0][1] for n,a in zip(range(3), LBL)]) > 0.6)

    acc = deconvolver.score(DFF,true_s.T>deconvolver.threshold)
    print(acc)
    
    clone(deconvolver)


if __name__ == '__main__':
    test_MedianFilterDetrender()
    test_SavGolFilterDetrender()
    test_CalciumDeconvolver()
    # test_params()

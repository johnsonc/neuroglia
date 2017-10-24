import numpy as np
from sklearn.base import TransformerMixin, BaseEstimator
from oasis.functions import deconvolve
from scipy.signal import medfilt, savgol_filter


class MedianFilterDetrend(BaseEstimator, TransformerMixin):
    """
    Median filter detrending
    """
    def __init__(self,
        window=101,
        peak_std_threshold=4):

        self.window = window
        self.peak_std_threshold = peak_std_threshold

    def robust_std(self, x):
        '''
        Robust estimate of std
        '''
        MAD = np.median(np.abs(x - np.median(x)))
        return 1.4826*MAD

    def fit(self, X, y=None):
        self.fit_params = {}
        return self

    def transform(self,X):
        X_new = X.copy()
        for col in X.columns:
            tmp_data = X[col].values.astype(np.double)
            mf = medfilt(tmp_data, self.window)
            mf = np.minimum(mf, self.peak_std_threshold * self.robust_std(mf))
            self.fit_params[col] = dict(mf=mf)
            X_new[col] = tmp_data - mf

        return X_new


class SavGolFilterDetrend(BaseEstimator, TransformerMixin):
    """
    Savitzky-Golay filter detrending
    """
    def __init__(self,
        window=201,
        order=3):

        self.window = window
        self.order = order

    def fit(self, X, y=None):
        self.fit_params = {}
        return self

    def transform(self,X):
        X_new = X.copy()
        for col in X.columns:
            tmp_data = X[col].values.astype(np.double)
            sgf = savgol_filter(tmp_data, self.window, self.order)
            self.fit_params[col] = dict(sgf=sgf)
            X_new[col] = tmp_data - sgf

        return X_new


class EventRescale(BaseEstimator, TransformerMixin):
    """
    Savitzky-Golay filter detrending
    """
    def __init__(self,
        log_transform=True,
        scale=5):

        self.log_transform = log_transform
        self.scale = scale

    def fit(self, X, y=None):
        self.fit_params = {}
        return self

    def transform(self,X):
        X_new = X.copy()
        for col in X.columns:
            tmp_data = X[col].values.astype(np.double)
            tmp_data *= self.scale
            if self.log_transform:
                tmp_data = np.log(1 + tmp_data)
            X_new[col] = tmp_data

        return X_new


class OASISInferer(BaseEstimator, TransformerMixin):
    """docstring for OASISInferer."""
    def __init__(self,
        output='spikes',
        g=(None,),
        sn=None,
        b=None,
        b_nonneg=True,
        optimize_g=0,
        penalty=0,
        **kwargs
        ):
        super(OASISInferer, self).__init__()

        self.output = output
        self.g = g
        self.sn = sn
        self.b = b
        self.b_nonneg = b_nonneg
        self.optimize_g = optimize_g
        self.penalty = penalty
        self.kwargs = kwargs

    def fit(self, X, y=None):
        self.fit_params = {}
        return self

    def transform(self,X):

        X_new = X.copy()

        for col in X.columns:
            c, s, b, g, lam = deconvolve(
                X[col].values.astype(np.double),
                g = self.g,
                sn = self.sn,
                b = self.b,
                b_nonneg = self.b_nonneg,
                optimize_g = self.optimize_g,
                penalty = self.penalty,
                **self.kwargs
                )
            self.fit_params[col] = dict(b=b,g=g,lam=lam,)

            if self.output=='denoised':
                X_new[col] = c
            elif self.output=='spikes':
                X_new[col] = np.maximum(0, s)
            else:
                raise NotImplementedError

        return X_new

class TraceTablizer(TransformerMixin):
    """SM: same as SpikeTabilizer, but for calcium traces from roi_traces.h5 or dff.h5 files
    converts an array of traces in the form of [[neuron0][neuron1]...[neuronN]] to a dataframe
    with "neuron" and "time" columns, sorted by "time" (in seconds)
    """
    def __init__(self):
        super(TraceTablizer, self).__init__()

    def fit(self, X, y=None):       # pragma: no cover
        return self

    def transform(self, X):
        f = h5py.File(X, 'r')
        data = np.asarray(f['data'])
        f.close()

        # column_names = ['neuron{}'.format(x) for x in np.arange(0,len(raw_traces), 1)]
        # df = pd.DataFrame(data, index = column_names).transpose()
        whole_seconds = int(len(data[0]) / 30)
        frame_dif = (len(data[0]) - (whole_seconds * 30))

        split_data = [np.split(data[x][frame_dif:], whole_seconds) for x in range(len(data))]
        data_s = [[np.mean(y) for y in split_data[x]] for x in range(len(split_data))]


        df = pd.DataFrame(data_s).transpose()
        return df


def normalize_trace(trace, window, percentile): 

    trace = pd.Series(trace)
    p = lambda x: np.percentile(x,percentile) # suggest 8% in literature, but this doesnt work well for our data, use median
    baseline = trace.rolling(window=window,center=True).apply(func=p)
    baseline = baseline.fillna(method='bfill')
    baseline = baseline.fillna(method='ffill')
    dF = trace-baseline

    dF = np.asarray(dF)   
    F = np.asarray(baseline)

    dFF = dF/F
    return dFF


class Normalize(BaseEstimator,TransformerMixin):
    """docstring for Normalize."""
    def __init__(self, window, percentile):
        super(Normalize, self).__init__()
        self.window = window
        self.percentile = percentile
        
    def fit(self, X, y=None):
        return self
    
    def transform(self,X):
        # this is where the magic happens

        df_norm = pd.DataFrame()
        for col in df.columns:
            df_norm[col] = normalize_trace(trace=df[col], window=180, percentile=8)

        return df_norm
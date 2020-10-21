# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""GP Tuner."""
import warnings
import numpy as np

from scipy.stats import norm
from scipy.optimize import minimize
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern

from mindinsight.optimizer.common.enums import AcquisitionFunctionEnum, HyperParamKey
from mindinsight.optimizer.common.log import logger
from mindinsight.optimizer.tuners.base_tuner import BaseTuner
from mindinsight.optimizer.utils.param_handler import generate_arrays, match_value_type
from mindinsight.optimizer.utils.transformer import Transformer
from mindinsight.utils.exceptions import ParamValueError


class AcquisitionFunction:
    """
    It can be seen from the Gaussian process that the probability description of the objective
    function can be obtained by sampling. Sampling usually involves two aspects:
        - Explore: Explore new spaces, this sampling helps to estimate more accurate results;
        - Exploit: Sampling near the existing results (usually near the existing maximum value),
          hoping to find larger results.

    The purpose of the acquisition function is to balance these two sampling processes.
    Supported acquisition function:
        - Probability of improvement.
        - Expected improvement.
        - Upper confidence bound. The weighted sum of posterior mean and posterior standard deviation.
          formula: result = exploitation + βt * exploration, where βt are appropriate constants.

    Args:
        method (str): The method for acquisition function, including 'ucb', 'pi', and 'ei'.
        beta (float): trade-off param for upper confidence bound function.
        beta_decay (float): the decay for beta. Formula: beta = beta * beta_decay.
        beta_decay_delay (int): if the counter is bigger than beta_decay_delay, the beta begins to decay.
        xi (float): trade-off for expected improvement and probability of improvement.
    """
    def __init__(self, method: str, beta, xi, beta_decay=1, beta_decay_delay=0):
        self._beta = beta
        self._beta_decay = beta_decay
        self._beta_decay_delay = beta_decay_delay
        self._xi = xi
        self._method = method.lower()
        if self._method not in AcquisitionFunctionEnum.list_members():
            raise ParamValueError(error_detail="The 'method' should be in %s." % AcquisitionFunctionEnum.list_members())

        self._counter = 0

    def update(self):
        """Update k."""
        self._counter += 1

        if self._counter > self._beta_decay_delay and self._beta_decay < 1:
            self._beta *= self._beta_decay

    def ac(self, x, gp, y_max):
        """Acquisition Function."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mean, std = gp.predict(x, return_std=True)

        if self._method == AcquisitionFunctionEnum.UCB.value:
            # Upper confidence bound.
            res = mean + self._beta * std
        elif self._method == AcquisitionFunctionEnum.EI.value:
            # Expected improvement.
            u_f = (mean - y_max - self._xi)
            z = u_f / std
            res = u_f * norm.cdf(z) + std * norm.pdf(z)
        else:
            # Probability of improvement.
            z = (mean - y_max - self._xi) / std
            res = norm.cdf(z)

        return res


class GPBaseTuner(BaseTuner):
    """
    Tuner using gaussian process regressor.

    Args:
        method (str): The method for acquisition function, including 'ucb', 'pi', and 'ei'.
            Detail at AcquisitionFunction.
        beta (float): β, trade-off param for upper confidence bound function.
        beta_decay (float): the decay for beta. beta = beta * beta_decay.
        beta_decay_delay (int): if counter is bigger than beta_decay_delay, the beta begins to decay.
        xi (float): ξ, trade-off for expected improvement and probability of improvement.
        random_state (np.random.RandomState): if it is None, it will be assigned as RandomState.
    """
    def __init__(self,
                 method=AcquisitionFunctionEnum.UCB.value,
                 beta=2.576,
                 beta_decay=1,
                 beta_decay_delay=0,
                 xi=0.0,
                 random_state=None):
        self._random_state = self._get_random_state(random_state)
        self._utility_function = AcquisitionFunction(method=method,
                                                     beta=beta,
                                                     xi=xi,
                                                     beta_decay=beta_decay,
                                                     beta_decay_delay=beta_decay_delay)
        self._gp = GaussianProcessRegressor(
            kernel=Matern(nu=2.5),
            alpha=1e-6,
            normalize_y=True,
            n_restarts_optimizer=5,
            random_state=self._random_state
        )

    def _get_random_state(self, random_state=None):
        """Get random state."""
        if random_state is not None and not isinstance(random_state, (int, np.random.RandomState)):
            raise ParamValueError("The 'random_state' should be None, integer or np.random.RandomState.")
        if not isinstance(random_state, np.random.RandomState):
            random_state = np.random.RandomState(random_state)
        return random_state

    def _acq_max(self, gp, y_max, bounds, params_info, n_warmup=10000, n_iter=10):
        """Get max try calculated by acquisition function."""
        x_tries = generate_arrays(params_info, n_warmup)
        ys = self._utility_function.ac(x_tries, gp=gp, y_max=y_max)
        x_max = x_tries[ys.argmax()]
        max_acq = ys.max()

        x_seeds = generate_arrays(params_info, n_iter)
        for x_try in x_seeds:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = minimize(lambda x: -self._utility_function.ac(x.reshape(1, -1), gp=gp, y_max=y_max),
                               x_try.reshape(1, -1), bounds=bounds, method="L-BFGS-B")

            if not res.success:
                continue

            if max_acq is None or -res.fun[0] >= max_acq:
                x_max = match_value_type(x_max, params_info)
                max_acq = -res.fun[0]

        return np.clip(x_max, bounds[:, 0], bounds[:, 1])

    def suggest(self, params, target, params_info: dict):
        """Get suggest values."""
        bounds = []
        for param_info in params_info.values():
            bound = param_info[HyperParamKey.BOUND.value] if HyperParamKey.BOUND.value in param_info \
                else param_info['choice']
            bounds.append([min(bound), max(bound)])
        bounds = np.array(bounds)

        min_lineage_rows = 2
        if not np.array(params).any() or params.shape[0] < min_lineage_rows:
            logger.info("Without valid histories or the rows of lineages < %s, "
                        "parameters will be recommended randomly.", min_lineage_rows)
            suggestion = generate_arrays(params_info)
        else:
            self._gp.fit(params, target)
            suggestion = self._acq_max(
                gp=self._gp,
                y_max=target.max(),
                bounds=bounds,
                params_info=params_info
            )

        suggestion, user_defined_info = Transformer.transform_list_to_dict(params_info, suggestion)
        return suggestion, user_defined_info

"""Forest based minimization algorithms."""

from sklearn.utils import check_random_state

from .base import base_minimize
from ..learning import ExtraTreesRegressor
from ..learning import RandomForestRegressor
from ..learning import RandomForestQuantileRegressor


def forest_minimize(func, dimensions, base_estimator="ET",
                    n_calls=100, n_random_starts=10,
                    acq_func="EI", acq_optimizer="auto",
                    x0=None, y0=None, random_state=None, verbose=False,
                    callback=None, n_points=10000, xi=0.01, kappa=1.96,
                    n_jobs=1, quantiles=0.05):
    """Sequential optimisation using decision trees.

    A tree based regression model is used to model the expensive to evaluate
    function `func`. The model is improved by sequentially evaluating
    the expensive function at the next best point. Thereby finding the
    minimum of `func` with as few evaluations as possible.

    The total number of evaluations, `n_calls`, are performed like the
    following. If `x0` is provided but not `y0`, then the elements of `x0`
    are first evaluated, followed by `n_random_starts` evaluations.
    Finally, `n_calls - len(x0) - n_random_starts` evaluations are
    made guided by the surrogate model. If `x0` and `y0` are both
    provided then `n_random_starts` evaluations are first made then
    `n_calls - n_random_starts` subsequent evaluations are made
    guided by the surrogate model.

    Parameters
    ----------
    * `func` [callable]:
        Function to minimize. Should take a array of parameters and
        return the function values.

    * `dimensions` [list, shape=(n_dims,)]:
        List of search space dimensions.
        Each search dimension can be defined either as

        - a `(upper_bound, lower_bound)` tuple (for `Real` or `Integer`
          dimensions),
        - a `(upper_bound, lower_bound, prior)` tuple (for `Real`
          dimensions),
        - as a list of categories (for `Categorical` dimensions), or
        - an instance of a `Dimension` object (`Real`, `Integer` or
          `Categorical`).

         NOTE: The upper and lower bounds are inclusive for `Integer`
         dimensions.

    * `base_estimator` [string or `Regressor`, default=`"ET"`]:
        The regressor to use as surrogate model. Can be either

        - `"RF"` for random forest regressor
        - `"ET"` for extra trees regressor
        - instance of regressor with support for `return_std` in its predict
          method

        The predefined models are initilized with good defaults. If you
        want to adjust the model parameters pass your own instance of
        a regressor which returns the mean and standard deviation when
        making predictions.

    * `n_calls` [int, default=100]:
        Number of calls to `func`.

    * `n_random_starts` [int, default=10]:
        Number of evaluations of `func` with random initialization points
        before approximating the `func` with `base_estimator`.

    * `acq_func` [string, default=`"LCB"`]:
        Function to minimize over the forest posterior. Can be either

        - `"LCB"` for lower confidence bound.
        - `"EI"` for negative expected improvement.
        - `"PI"` for negative probability of improvement.

    * `x0` [list, list of lists or `None`]:
        Initial input points.

        - If it is a list of lists, use it as a list of input points.
        - If it is a list, use it as a single initial input point.
        - If it is `None`, no initial input points are used.

    * `y0` [list, scalar or `None`]:
        Evaluation of initial input points.

        - If it is a list, then it corresponds to evaluations of the function
          at each element of `x0` : the i-th element of `y0` corresponds
          to the function evaluated at the i-th element of `x0`.
        - If it is a scalar, then it corresponds to the evaluation of the
          function at `x0`.
        - If it is None and `x0` is provided, then the function is evaluated
          at each element of `x0`.

    * `random_state` [int, RandomState instance, or None (default)]:
        Set random state to something other than None for reproducible
        results.

    * `verbose` [boolean, default=False]:
        Control the verbosity. It is advised to set the verbosity to True
        for long optimization runs.

    * `callback` [callable, optional]
        If provided, then `callback(res)` is called after call to func.

    * `n_points` [int, default=10000]:
        Number of points to sample when minimizing the acquisition function.

    * `xi` [float, default=0.01]:
        Controls how much improvement one wants over the previous best
        values. Used when the acquisition is either `"EI"` or `"PI"`.

    * `kappa` [float, default=1.96]:
        Controls how much of the variance in the predicted values should be
        taken into account. If set to be very high, then we are favouring
        exploration over exploitation and vice versa.
        Used when the acquisition is `"LCB"`.

    * `n_jobs` [int, default=1]:
        The number of jobs to run in parallel for `fit` and `predict`.
        If -1, then the number of jobs is set to the number of cores.

    Returns
    -------
    * `res` [`OptimizeResult`, scipy object]:
        The optimization result returned as a OptimizeResult object.
        Important attributes are:

        - `x` [list]: location of the minimum.
        - `fun` [float]: function value at the minimum.
        - `models`: surrogate models used for each iteration.
        - `x_iters` [list of lists]: location of function evaluation for each
           iteration.
        - `func_vals` [array]: function value for each iteration.
        - `space` [Space]: the optimization space.
        - `specs` [dict]`: the call specifications.

        For more details related to the OptimizeResult object, refer
        http://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.OptimizeResult.html
    """
    rng = check_random_state(random_state)

    # Default estimator
    if isinstance(base_estimator, str):
        if base_estimator not in ("RF", "ET", "RFquantile"):
            raise ValueError(
                "Valid strings for the base_estimator parameter"
                " are: 'RF' or 'ET', not '%s'" % base_estimator)

        if base_estimator == "RF":
            base_estimator = RandomForestRegressor(n_estimators=100,
                                                   min_samples_leaf=3,
                                                   n_jobs=n_jobs,
                                                   random_state=rng)

        elif base_estimator == "ET":
            base_estimator = ExtraTreesRegressor(n_estimators=100,
                                                 min_samples_leaf=3,
                                                 n_jobs=n_jobs,
                                                 random_state=rng)
        elif base_estimator == "RFquantile":
            base_estimator = RandomForestQuantileRegressor(quantiles=quantiles,
                                                           n_estimators=100,
                                                           min_samples_leaf=3,
                                                           n_jobs=n_jobs,
                                                           random_state=rng)

    return base_minimize(func, dimensions, base_estimator,
                         n_calls=n_calls, n_points=n_points,
                         n_random_starts=n_random_starts,
                         x0=x0, y0=y0, random_state=random_state,
                         acq_func=acq_func,
                         xi=xi, kappa=kappa, verbose=verbose,
                         callback=callback, acq_optimizer="sampling")

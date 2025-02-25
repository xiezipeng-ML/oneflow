"""
Copyright 2020 The OneFlow Authors. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
from typing import Optional, Union

import oneflow._oneflow_internal
from oneflow.compatible import single_client as flow
from oneflow.compatible.single_client.framework import id_util as id_util
from oneflow.compatible.single_client.framework import remote_blob as remote_blob_util


def build_math_binary_elementwise_op(math_op, x, y, name=None):
    if name is None:
        name = id_util.UniqueStr(math_op + "_")
    return (
        flow.user_op_builder(name)
        .Op(math_op)
        .Input("x", [x])
        .Input("y", [y])
        .Output("z")
        .Build()
        .InferAndTryRun()
        .RemoteBlobList()[0]
    )


def atan2(
    x: oneflow._oneflow_internal.BlobDesc,
    y: oneflow._oneflow_internal.BlobDesc,
    name: Optional[str] = None,
) -> oneflow._oneflow_internal.BlobDesc:
    """This operator computes the values of :math:`arctan(\\frac{x}{y})`.

    The equation is:

    .. math::

        out = arctan(\\frac{x}{y})

    Args:
        x (oneflow._oneflow_internal.BlobDesc): A Blob
        y (oneflow._oneflow_internal.BlobDesc): A Blob
        name (Optional[str], optional): The name for the operation. Defaults to None.

    Returns:
        oneflow._oneflow_internal.BlobDesc: The result Blob

    For example:

    .. code-block:: python

        import oneflow.compatible.single_client as flow
        import numpy as np
        import oneflow.compatible.single_client.typing as tp


        @flow.global_function()
        def atan2Job(x: tp.Numpy.Placeholder((3,),), y: tp.Numpy.Placeholder((3, ))
        )-> tp.Numpy:
            return flow.math.atan2(x, y)

        x = np.array([1, 2, 3]).astype(np.float32)
        y = np.array([4, 4, 4]).astype(np.float32)
        out = atan2Job(x, y)


        # out [0.24497867 0.4636476  0.6435011 ]
        # We take the first value as an example
        # (arctan(1/4) * pi) / 180 = 0.24497867

    """
    return build_math_binary_elementwise_op("atan2", x, y, name)


def pow(
    x: oneflow._oneflow_internal.BlobDesc,
    y: Union[oneflow._oneflow_internal.BlobDesc, float],
    name: Optional[str] = None,
) -> oneflow._oneflow_internal.BlobDesc:
    """This operator computes the Pow result.

    The equation is:

    .. math::

        out = x^y

    Args:
        x (oneflow._oneflow_internal.BlobDesc): A Blob
        y (Union[oneflow._oneflow_internal.BlobDesc, float]): A Blob or float value, the exponential factor of Pow
        name (Optional[str], optional): The name for the operation. Defaults to None.

    Returns:
        oneflow._oneflow_internal.BlobDesc: The result Blob

    For example:

    Example 1:

    .. code-block:: python

        import oneflow.compatible.single_client as flow
        import numpy as np
        import oneflow.compatible.single_client.typing as tp


        @flow.global_function()
        def powJob(x: tp.Numpy.Placeholder((3,), ), y: tp.Numpy.Placeholder((3,))
                ) -> tp.Numpy:
            return flow.math.pow(x, y)


        x = np.array([2, 3, 4]).astype(np.float32)
        y = np.array([2, 3, 4]).astype(np.float32)
        out = powJob(x, y)

        # out [  4.  27. 256.]

    Example 2:

    .. code-block:: python

        import oneflow.compatible.single_client as flow
        import oneflow.compatible.single_client.typing as tp
        import numpy as np


        @flow.global_function()
        def scalar_pow_job(x: tp.Numpy.Placeholder(shape=(3, )))->tp.Numpy:
            with flow.scope.placement("cpu", "0:0"):
                out = flow.math.pow(x, 2.0)
            return out


        x = np.array([1, 2, 3]).astype(np.float32)
        out = scalar_pow_job(x)

        # out [1. 4. 9.]
    """
    if name is None:
        name = id_util.UniqueStr("Pow_")
    if isinstance(y, (int, float)):
        return (
            flow.user_op_builder(name)
            .Op("scalar_pow")
            .Input("in", [x])
            .Attr("exponent", float(y))
            .Output("out")
            .Build()
            .InferAndTryRun()
            .RemoteBlobList()[0]
        )
    else:
        return build_math_binary_elementwise_op("pow", x, y, name)


def floordiv(
    x: oneflow._oneflow_internal.BlobDesc,
    y: oneflow._oneflow_internal.BlobDesc,
    name: Optional[str] = None,
) -> oneflow._oneflow_internal.BlobDesc:
    """This operator computes the result of :math:`x/y`, rounding toward the most negative integer value

    Args:
        x (oneflow._oneflow_internal.BlobDesc): A Blob
        y (oneflow._oneflow_internal.BlobDesc): A Blob
        name (Optional[str], optional): The name for the operation. Defaults to None.

    Returns:
        oneflow._oneflow_internal.BlobDesc: The result Blob

    For example:

    .. code-block:: python

        import oneflow.compatible.single_client as flow
        import numpy as np
        import oneflow.compatible.single_client.typing as tp


        @flow.global_function()
        def floor_div_Job(x: tp.Numpy.Placeholder((3,)),
                        y: tp.Numpy.Placeholder((3,))
        ) -> tp.Numpy:
            return flow.math.floordiv(x, y)


        x = np.array([4, 3, 5]).astype(np.float32)
        y = np.array([3, 2, 2]).astype(np.float32)
        out = floor_div_Job(x, y)

        # out [1. 1. 2.]
    """
    return build_math_binary_elementwise_op("floordiv", x, y, name)


def xdivy(
    x: oneflow._oneflow_internal.BlobDesc,
    y: oneflow._oneflow_internal.BlobDesc,
    name: Optional[str] = None,
) -> oneflow._oneflow_internal.BlobDesc:
    """This operator computes the result of :math:`x/y`

    Args:
        x (oneflow._oneflow_internal.BlobDesc): A Blob
        y (oneflow._oneflow_internal.BlobDesc): A Blob
        name (Optional[str], optional): The name for the operation. Defaults to None.

    Returns:
        oneflow._oneflow_internal.BlobDesc: The result Blob

    For example:

    .. code-block:: python

        import oneflow.compatible.single_client as flow
        import numpy as np
        import oneflow.compatible.single_client.typing as tp


        @flow.global_function()
        def xdivy_Job(x: tp.Numpy.Placeholder((3,)),
                        y: tp.Numpy.Placeholder((3,))
        ) -> tp.Numpy:
            return flow.math.xdivy(x, y)


        x = np.array([4, 3, 5]).astype(np.float32)
        y = np.array([3, 2, 2]).astype(np.float32)
        out = xdivy_Job(x, y)

        # out [1.3333334 1.5       2.5      ]

    """
    return build_math_binary_elementwise_op("xdivy", x, y, name)


def xlogy(
    x: oneflow._oneflow_internal.BlobDesc,
    y: oneflow._oneflow_internal.BlobDesc,
    name: Optional[str] = None,
) -> oneflow._oneflow_internal.BlobDesc:
    """This operator computes the result of :math:`x*log(y)`

    Args:
        x (oneflow._oneflow_internal.BlobDesc): A Blob
        y (oneflow._oneflow_internal.BlobDesc): A Blob
        name (Optional[str], optional): The name for the operation. Defaults to None.

    Returns:
        oneflow._oneflow_internal.BlobDesc: The result Blob

    For example:

    .. code-block:: python

        import oneflow.compatible.single_client as flow
        import numpy as np
        import oneflow.compatible.single_client.typing as tp


        @flow.global_function()
        def xlogy_Job(x: tp.Numpy.Placeholder((3,)),
                    y: tp.Numpy.Placeholder((3,))
        ) -> tp.Numpy:
            return flow.math.xlogy(x, y)


        x = np.array([2, 2, 2]).astype(np.float32)
        y = np.array([4, 8, 16]).astype(np.float32)
        out = xlogy_Job(x, y)

        # out [2.7725887 4.158883  5.5451775]
    """
    return build_math_binary_elementwise_op("xlogy", x, y, name)

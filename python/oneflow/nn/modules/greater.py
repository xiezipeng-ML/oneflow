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
import oneflow as flow
from oneflow.framework.tensor import register_tensor_op
from oneflow.nn.module import Module


class Greater(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, y):
        if x.dtype != flow.float32:
            x = flow.cast(x, flow.float32)
        if isinstance(y, int) or isinstance(y, float):
            y = flow.Tensor(
                [float(y)], dtype=flow.float32, device=flow.device(x.device.type)
            )
        if y.dtype != flow.float32:
            y = flow.cast(y, flow.float32)
        return flow.F.broadcast_greater(x, y)


def greater_op(x, y):
    """Returns the truth value of :math:`x > y` element-wise.

    Args:
        x (oneflow.Tensor): A Tensor
        y (oneflow.Tensor): A Tensor

    Returns:
        oneflow.Tensor: A Tensor with int8 type.

    For example:

    .. code-block:: python

        >>> import numpy as np
        >>> import oneflow as flow
        
        >>> input1 = flow.Tensor(np.random.randn(2, 6, 5, 3), dtype=flow.float32)
        >>> input2 = flow.Tensor(np.random.randn(2, 6, 5, 3), dtype=flow.float32)

        >>> out = flow.gt(input1, input2).shape
        >>> out
        flow.Size([2, 6, 5, 3])

    """
    return Greater()(x, y)


@register_tensor_op("gt")
def greater_op_tensor(x, y):
    """

    gt() -> Tensor

    See :func:`oneflow.gt`

    """
    return Greater()(x, y)


if __name__ == "__main__":
    import doctest

    doctest.testmod(raise_on_error=True)

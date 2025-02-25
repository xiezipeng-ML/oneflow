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
import collections
from typing import Optional, Sequence, Union

import oneflow as flow
from oneflow.framework.tensor import register_tensor_op
from oneflow.nn.module import Module
from oneflow.nn.modules.utils import _check_axis, _check_inplace_valid
from oneflow.ops.transpose_util import (
    get_inversed_perm,
    get_perm_when_transpose_axis_to_last_dim,
)


class ScalarMul(Module):
    def __init__(self, alpha) -> None:
        super().__init__()
        if not isinstance(alpha, (int, float)):
            raise ValueError("alpha type can only be int or float")
        self.alpha = alpha

    def forward(self, x):
        return flow.F.mul_scalar(x, self.alpha)


class ScalarMulByTensor(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, y):
        return flow.F.mul_scalar_by_tensor(x, y)


class ElementwiseMul(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, y):
        return flow.F.mul(x, y)


class BroadcastMul(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, y):
        return flow.F.broadcast_mul(x, y)


@register_tensor_op("mul")
def _mul(input, other):
    """Computes the multiplication of input by other for each element, scalar and broadcast promotation are supported.
    
    The formula is:

    .. math::
        out = input \\times other
    
    For example:

    .. code-block:: python

        >>> import numpy as np
        >>> import oneflow as flow
        
        # element-wise multiply
        >>> input = flow.Tensor(np.random.randn(2,3))
        >>> other = flow.Tensor(np.random.randn(2,3))
        >>> out = flow.mul(input,other).numpy()
        >>> out.shape
        (2, 3)

        # scalar mutiply
        >>> input = 5
        >>> other = flow.Tensor(np.random.randn(2,3))
        >>> out = flow.mul(input,other).numpy()
        >>> out.shape
        (2, 3)

        # broadcast mutiply
        >>> input = flow.Tensor(np.random.randn(1,1))
        >>> other = flow.Tensor(np.random.randn(2,3))
        >>> out = flow.mul(input,other).numpy()
        >>> out.shape 
        (2, 3)

    """
    if isinstance(input, (int, float)):
        return ScalarMul(input)(other)
    elif isinstance(other, (int, float)):
        return ScalarMul(other)(input)
    elif input.shape == other.shape:
        return ElementwiseMul()(input, other)
    elif input.shape == (1,):
        return ScalarMulByTensor()(other, input)
    elif other.shape == (1,):
        return ScalarMulByTensor()(input, other)
    else:
        return BroadcastMul()(input, other)


class Variance(Module):
    def __init__(self, dim: int = None, keepdim: bool = False) -> None:
        super().__init__()
        self.dim = dim
        self.keepdim = keepdim

    def forward(self, input):
        axis = _check_axis(self.dim, input.shape)
        if isinstance(axis, list) and len(axis) == 0:
            return flow.zeros(size=input.shape)
        else:
            return flow.sub(
                flow.mean(flow.square(input), axis, self.keepdim),
                flow.square(flow.mean(input, axis, self.keepdim)),
            )


@register_tensor_op("var")
def variance_op(input, dim=None, keepdim=False):
    """Returns the variance of each row of the `input` tensor in the given dimension `dim`.

    If `keepdim` is `True`, the output tensor is of the same size as `input` except in the dimension(s) `dim` 
    where it is of size 1. Otherwise, dim is squeezed (see `flow.squeeze()`), resulting in the output 
    tensor having 1 (or `len(dim)`) fewer dimension(s).

    Args:
        input (Tensor): the input tensor.
        dim (int or tuple of python:ints): the dimension or dimensions to reduce. Defaults to None.
        keepdim (bool, optional): whether the output tensor has dim retained or not. Defaults to False.

    Returns:
        Tensor: The result of variance on the specified axis of input Tensor

    For example:

    .. code-block:: python

        >>> import numpy as np
        >>> import oneflow as flow
        
        >>> np_arr = np.random.randn(2,3,4,5)
        >>> input = flow.Tensor(np_arr)
        >>> output = flow.var(input, 1, True)

    """
    return Variance(dim, keepdim)(input)


class ScalarSubByTensor(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, y):
        return flow.F.sub_scalar_by_tensor(x, y)


class BroadcastSub(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, y):
        return flow.F.broadcast_sub(x, y)


def scalar_add_inplaceable(x, alpha, inplace: bool = False):
    if inplace:
        _check_inplace_valid(x)
    return flow.F.add_scalar(x, alpha, inplace)


@register_tensor_op("sub")
def _sub(input, other):
    """Computes the subtraction of input by other for each element, scalar and broadcast promotation are supported.
    The formula is:

    .. math::
        out = input - other
    
    For example:

    .. code-block:: python

        >>> import numpy as np
        >>> import oneflow as flow
        
        # element-wise subtract
        >>> input = flow.Tensor(np.random.randn(2,3))
        >>> other = flow.Tensor(np.random.randn(2,3))
        >>> out = flow.sub(input,other).numpy()
        >>> out.shape
        (2, 3)

        # scalar subtract
        >>> input = 5
        >>> other = flow.Tensor(np.random.randn(2,3))
        >>> out = flow.sub(input,other).numpy()
        >>> out.shape
        (2, 3)

        # broadcast subtract
        >>> input = flow.Tensor(np.random.randn(1,1))
        >>> other = flow.Tensor(np.random.randn(2,3))
        >>> out = flow.sub(input,other).numpy()
        >>> out.shape
        (2, 3)

    """
    if isinstance(input, (int, float)):
        return flow.F.add_scalar(ScalarMul(-1)(other), input)
    elif isinstance(other, (int, float)):
        return flow.F.add_scalar(input, -1 * other)
    elif input.shape == other.shape:
        return BroadcastSub()(input, other)
    elif other.shape == (1,):
        return ScalarSubByTensor()(input, other)
    else:
        return BroadcastSub()(input, other)


class BroadcastDiv(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, y):
        return flow.F.broadcast_div(x, y)


class ScalarDivByTensor(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, scalar):
        return flow.F.div_scalar_by_tensor(x, scalar)


@register_tensor_op("div")
def _div(input, other):
    """Computes the division of input by other for each element, scalar and broadcast promotation are supported.
    The formula is:

    .. math::
        out = \\frac{input}{other}
    
    Args:
        input (Union[int, float, flow.Tensor]): input.
        other (Union[int, float, flow.Tensor]): other.
    
    For example:

    .. code-block:: python

        >>> import numpy as np
        >>> import oneflow as flow
        
        # element-wise divide
        >>> input = flow.Tensor(np.random.randn(2,3))
        >>> other = flow.Tensor(np.random.randn(2,3))
        >>> out = flow.div(input,other).numpy()
        >>> out.shape
        (2, 3)

        # scalar divide
        >>> input = 5
        >>> other = flow.Tensor(np.random.randn(2,3))
        >>> out = flow.div(input,other).numpy()
        >>> out.shape
        (2, 3)

        # broadcast divide
        >>> input = flow.Tensor(np.random.randn(1,1))
        >>> other = flow.Tensor(np.random.randn(2,3))
        >>> out = flow.div(input,other).numpy()
        >>> out.shape 
        (2, 3)

    """
    if isinstance(input, (int, float)):
        return ScalarMul(input)(flow.reciprocal(other))
    elif isinstance(other, (int, float)):
        if other == 0 or other == 0.0:
            other = 0.0
        else:
            other = 1.0 / float(other)
        return ScalarMul(other)(input)
    elif input.shape == other.shape:
        return BroadcastDiv()(input, other)
    elif other.shape == (1,):
        return ScalarDivByTensor()(input, other)
    else:
        return BroadcastDiv()(input, other)


class Reciprocal(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x):
        return flow.F.reciprocal_no_nan(x)


@register_tensor_op("reciprocal")
def _reciprocal(x):
    """Computes the safe reciprocal of x. If x is zero, the reciprocal will
    be also set to zero.

    For example:

    .. code-block:: python

        >>> import numpy as np
        >>> import oneflow as flow
        
        >>> x = flow.Tensor(np.array([[1, 2, 3], [4, 5, 6]]))
        >>> out = flow.reciprocal(x)
        >>> out.numpy()
        array([[1.        , 0.5       , 0.33333334],
               [0.25      , 0.2       , 0.16666667]], dtype=float32)
    """
    return Reciprocal()(x)


def scalar_add_by_tensor_inplaceable(x, y, inplace: bool = False):
    if inplace:
        _check_inplace_valid(x)
    return flow.F.add_scalar_by_tensor(x, y, inplace)


def elementwise_add_inplaceable(x, y, inplace: bool = False):
    if inplace:
        _check_inplace_valid(x)
    return flow.F.add(x, y, inplace)


@register_tensor_op("add")
def _add(x, y):
    """Computes the addition of x by y for each element, scalar and broadcast promotation are supported.
    The formula is:

    .. math::
        out = x + y

    For example:

    .. code-block:: python

        >>> import numpy as np
        >>> import oneflow as flow
        
        # element-wise add
        >>> x = flow.Tensor(np.random.randn(2,3))
        >>> y = flow.Tensor(np.random.randn(2,3))
        >>> out = flow.add(x, y).numpy()
        >>> out.shape
        (2, 3)

        # scalar add
        >>> x = 5
        >>> y = flow.Tensor(np.random.randn(2,3))
        >>> out = flow.add(x, y).numpy()
        >>> out.shape
        (2, 3)

        # broadcast add
        >>> x = flow.Tensor(np.random.randn(1,1))
        >>> y = flow.Tensor(np.random.randn(2,3))
        >>> out = flow.add(x, y).numpy()
        >>> out.shape
        (2, 3)

    """
    if isinstance(x, (int, float)):
        return flow.F.add_scalar(y, x, False)
    elif isinstance(y, (int, float)):
        return flow.F.add_scalar(x, y, False)
    elif x.shape == y.shape:
        return flow.F.add(x, y, False)
    elif x.shape == (1,):
        return flow.F.add_scalar_by_tensor(y, x, False)
    elif y.shape == (1,):
        return flow.F.add_scalar_by_tensor(x, y, False)
    else:
        return flow.F.broadcast_add(x, y)


@register_tensor_op("add_")
def _add_inplace(x, y):
    """
    In-place version of :func:`oneflow.Tensor.add`.
    """
    if isinstance(y, (int, float)):
        return scalar_add_inplaceable(x, y, inplace=True)
    elif x.shape == y.shape:
        return elementwise_add_inplaceable(x, y, inplace=True)
    elif x.shape == (1,):
        raise RuntimeError(
            f"output with shape {x.shape} doesn't match the broadcast shape {y.shape}"
        )
    elif y.shape == (1,):
        return scalar_add_by_tensor_inplaceable(x, y, inplace=True)
    else:
        y = flow.broadcast_like(y, x)
        return elementwise_add_inplaceable(x, y, inplace=True)


class Asin(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x):
        return flow.F.asin(x)


def asin_op(input):
    """
    Returns a new tensor with the arcsine of the elements of :attr:`input`.

    .. math::
        \\text{out}_{i} = \\sin^{-1}(\\text{input}_{i})

    Args:
        input (Tensor): the input tensor.

    For example:

    .. code-block:: python

        >>> import oneflow as flow
        >>> import numpy as np
        >>> input = flow.Tensor(np.array([-0.5,  0.8, 1.0,  -0.8]), dtype=flow.float32)
        >>> output = flow.asin(input)
        >>> output.shape
        flow.Size([4])
        >>> output
        tensor([-0.5236,  0.9273,  1.5708, -0.9273], dtype=oneflow.float32)
        >>> input1 = flow.Tensor(np.array([[0.8, 1.0], [-0.6, -1.0]]), dtype=flow.float32)
        >>> output1 = input1.asin()
        >>> output1.shape
        flow.Size([2, 2])
        >>> output1
        tensor([[ 0.9273,  1.5708],
                [-0.6435, -1.5708]], dtype=oneflow.float32)
    """
    return Asin()(input)


@register_tensor_op("asin")
def asin_op_tensor(input):
    """

    See :func:`oneflow.asin`
    """
    return Asin()(input)


def arcsin_op(input):
    """
  
    Alias for :func:`oneflow.asin`
    """
    return Asin()(input)


@register_tensor_op("arcsin")
def arcsin_op_tensor(input):
    """

    See :func:`oneflow.asin`
    """
    return Asin()(input)


class Asinh(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x):
        return flow.F.asinh(x)


def asinh_op(input):
    """
    Returns a new tensor with the inverse hyperbolic sine of the elements of :attr:`input`.

    .. math::
        \\text{out}_{i} = \\sinh^{-1}(\\text{input}_{i})

    Args:
        input (Tensor): the input tensor.

    For example:

    .. code-block:: python

        >>> import oneflow as flow
        >>> import numpy as np
        >>> input = flow.Tensor(np.array([2, 3, 4]), dtype=flow.float32)
        >>> output = flow.asinh(input)
        >>> output.shape
        flow.Size([3])
        >>> output
        tensor([1.4436, 1.8184, 2.0947], dtype=oneflow.float32)

        >>> input1 = flow.Tensor(np.array([[-1, 0, -0.4], [5, 7, 0.8]]), dtype=flow.float32)
        >>> output1 = input1.asinh()
        >>> output1.shape
        flow.Size([2, 3])
        >>> output1
        tensor([[-0.8814,  0.    , -0.39  ],
                [ 2.3124,  2.6441,  0.7327]], dtype=oneflow.float32)

    """
    return Asinh()(input)


def arcsinh_op(input):
    """
  
    Alias for :func:`oneflow.asinh`
    """
    return Asinh()(input)


@register_tensor_op("asinh")
def asinh_op_tensor(input):
    """

    See :func:`oneflow.asinh`
    """
    return Asinh()(input)


@register_tensor_op("arcsinh")
def arcsinh_op_tensor(input):
    """

    See :func:`oneflow.asinh`
    """
    return Asinh()(input)


class Sin(Module):
    def __init__(self, inplace: bool = False) -> None:
        super().__init__()
        self.inplace = inplace

    def forward(self, x):
        if self.inplace:
            _check_inplace_valid(x)
        return flow.F.sin(x, self.inplace)


def sin_op(tensor):
    """
    Returns a new tensor with the sine of the elements of :attr:`input`.

    .. math::

        \\text{out}_{i} = \\sin(\\text{input}_{i})

    Args:
        input (Tensor): the input tensor.

    For example:

    .. code-block:: python

        >>> import oneflow as flow
        >>> import numpy as np
        >>> x1 = flow.Tensor(np.array([-0.5461,  0.1347, -2.7266, -0.2746]).astype(np.float32))
        >>> out1 = flow.sin(x1)
        >>> out1
        tensor([-0.5194,  0.1343, -0.4032, -0.2712], dtype=oneflow.float32)
        >>> x2 = flow.Tensor(np.array([-1.4, 2.6, 3.7]).astype(np.float32),device=flow.device('cuda'))
        >>> out2 = flow.sin(x2)
        >>> out2
        tensor([-0.9854,  0.5155, -0.5298], device='cuda:0', dtype=oneflow.float32)

    """
    return Sin(inplace=False)(tensor)


@register_tensor_op("sin")
def sin_op_tensor(tensor):
    """

    sin() -> Tensor

    See :func:`oneflow.sin`
    
    """
    return Sin(inplace=False)(tensor)


@register_tensor_op("sin_")
def inplace_sin_op_tensor(x):
    """
    In-place version of :func:`oneflow.sin`
    
    """
    return Sin(inplace=True)(x)


class Cos(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x):
        return flow.F.cos(x)


@register_tensor_op("cos")
def cos_op(tensor):
    """
    Returns a new tensor with the cosine  of the elements of :attr:`input`.
    
    .. math::
        \\text{out}_{i} = \\cos(\\text{input}_{i})

    Args:
        input (Tensor): the input tensor.

    For example:

    .. code-block:: python

        >>> import oneflow as flow
        >>> import numpy as np
        >>> arr = np.array([1.4309,  1.2706, -0.8562,  0.9796])
        >>> input = flow.Tensor(arr, dtype=flow.float32)
        >>> output = flow.cos(input).numpy()

    """
    return Cos()(tensor)


class Atan(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x):
        return flow.F.atan(x)


def atan_op(tensor):
    """
    Returns a new tensor with the arctangent of the elements of :attr:`input`.

    .. math::
        \\text{out}_{i} = \\tan^{-1}(\\text{input}_{i})

    Args:
        input (Tensor): the input tensor.

    For example:

    .. code-block:: python
    
        >>> import oneflow as flow
        >>> import numpy as np
        >>> input = flow.Tensor(np.array([0.5, 0.6, 0.7]), dtype=flow.float32)
        >>> output = flow.atan(input)
        >>> output.shape
        flow.Size([3])
        
    """
    return Atan()(tensor)


@register_tensor_op("atan")
def atan_op_tensor(tensor):
    """

    See :func:`oneflow.atan`
    
    """
    return Atan()(tensor)


def arctan_op(tensor):
    """
    Alias for :func:`oneflow.atan`
    
    """
    return Atan()(tensor)


@register_tensor_op("arctan")
def arctan_op_tensor(tensor):
    """

    See :func:`oneflow.arctan`
    
    """
    return Atan()(tensor)


class FMod(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, y):
        if not isinstance(x, (flow.Tensor, flow._oneflow_internal.Tensor)):
            raise ValueError("Expected type of input is Tensor")
        if isinstance(y, (int, float)):
            x = flow.F.cast(x, flow.float32)
            y = flow.tensor([y], dtype=flow.float32, device=x.device)
        elif isinstance(y, (flow.Tensor, flow._oneflow_internal.Tensor)):
            if x.dtype != y.dtype:
                x = flow.F.cast(x, flow.float32)
                y = flow.F.cast(y, flow.float32)
        else:
            raise ValueError("Expected type of other is Tensor or Scalar")
        return flow.F.fmod(x, y)


def fmod_op(input, other):
    """
    fmod(input, other, *, out=None) -> Tensor

    Computes the element-wise remainder of division.

    The dividend and divisor may contain both for integer and floating point
    numbers. The remainder has the same sign as the dividend :attr:`input`.

    Supports broadcasting to a common shape, integer and float inputs.


    Args:
        input (Tensor): the dividend
        other (Tensor or Scalar): the divisor

    Keyword args:
        out (Tensor, optional): the output tensor.

    Example::

        >>> import oneflow as flow
        >>> flow.fmod(flow.tensor([-3., -2, -1, 1, 2, 3]), 2)
        tensor([-1., -0., -1.,  1.,  0.,  1.], dtype=oneflow.float32)
        >>> flow.fmod(flow.tensor([1, 2, 3, 4, 5]), 1.5)
        tensor([1. , 0.5, 0. , 1. , 0.5], dtype=oneflow.float32)
        >>> flow.fmod(flow.tensor([1, 2, 3, 4, -5]), flow.tensor([4, 2, 1, 3., 1]))
        tensor([ 1.,  0.,  0.,  1., -0.], dtype=oneflow.float32)

    """
    return FMod()(input, other)


@register_tensor_op("fmod")
def fmod_op_tensor(input, other):
    """

    See :func:`oneflow.fmod`
    
    """
    return FMod()(input, other)


class Log(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x):
        return flow.F.log(x)


@register_tensor_op("log")
def log_op(tensor):
    """
    Returns a new tensor with the natural logarithm of the elements of :attr:`input`.
    
    .. math::
        y_{i} = \\log_{e} (x_{i})

    Args:
        input (Tensor): the input tensor.
    
    For example:

    .. code-block:: python

        >>> import oneflow as flow
        >>> import numpy as np
        >>> arr = np.random.randn(2, 3, 4, 5)
        >>> input = flow.Tensor(arr, dtype=flow.float32)
        >>> output = flow.log(input)


    """
    return Log()(tensor)


class Subtract(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, y):
        if isinstance(x, (int, float)):
            return flow.F.add_scalar(-1 * y, x)
        elif isinstance(y, (int, float)):
            return flow.F.add_scalar(x, -1 * y)
        elif x.shape == y.shape:
            return BroadcastSub()(x, y)
        elif x.shape == (1,):
            return ScalarSubByTensor()(y, x)
        elif y.shape == (1,):
            return ScalarSubByTensor()(x, y)
        else:
            return BroadcastSub()(x, y)


class Sqrt(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, input):
        return flow.F.sqrt(input)


@register_tensor_op("rsqrt")
def rsqrt_op(input):
    """Returns a new tensor with the reciprocal of the square-root of each of
        the elements of :attr:`input`.

        .. math::
            \\text{out}_{i} = \\frac{1}{\\sqrt{\\text{input}_{i}}}

        Args:
            input (Tensor) – the input tensor.

         For example:

        .. code-block:: python

            >>> import oneflow as flow
            >>> import numpy as np
            
            >>> a = flow.Tensor(np.array([1.0, 2.0, 3.0]))
            >>> out = flow.rsqrt(a).numpy()
            >>> out
            array([1.        , 0.70710677, 0.57735026], dtype=float32)
    """
    return Rsqrt()(input)


class Rsqrt(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, input):
        return flow.F.rsqrt(input)


@register_tensor_op("sqrt")
def sqrt_op(input):
    """Returns a new tensor with the square-root of the elements of :attr:`input`.

        .. math::
            \\text{out}_{i} = \\sqrt{\\text{input}_{i}}

        Args:
            input (Tensor): the input tensor.

         For example:

        .. code-block:: python

            >>> import oneflow as flow
            >>> import numpy as np
            
            >>> arr = np.array([1.0, 2.0, 3.0])
            >>> input = flow.Tensor(arr)
            >>> output = flow.sqrt(input).numpy()
            >>> output
            array([1.       , 1.4142135, 1.7320508], dtype=float32)
        """
    return Sqrt()(input)


class Square(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, input):
        return flow.F.square(input)


@register_tensor_op("square")
def square_op(input):
    """Returns a new tensor with the square of the elements of :attr:`input`.

        .. math::
            \\text{out}_{i} = \\sqrt{\\text{input}_{i}}

        Args:
            input (Tensor): the input tensor.

         For example:

        .. code-block:: python

            >>> import oneflow as flow
            >>> import numpy as np
            
            >>> arr = np.array([1.0, 2.0, 3.0])
            >>> input = flow.Tensor(arr)
            >>> output = flow.square(input).numpy()
            >>> output
            array([1., 4., 9.], dtype=float32)
        """
    return Square()(input)


class Std(Module):
    def __init__(self, dim=None, unbiased=False, keepdim=False) -> None:
        super().__init__()
        assert unbiased == False, "Only support 'unbiased=False' for now!"
        self.unbiased = unbiased
        self.keepdim = keepdim
        self.dim = dim
        self.reduce_count = 1
        self.square_op = Square()
        self.sqrt_op = Sqrt()
        self.subtract_op = Subtract()

    def forward(self, x):
        self.axis = _check_axis(self.dim, x.shape)
        if isinstance(self.axis, list) and len(self.axis) == 0:
            return flow.zeros(size=x.shape)
        else:
            if len(self.axis) == 0:
                self.reduce_count = x.nelement()
            else:
                for i in self.axis:
                    self.reduce_count *= x.shape[i]
            sum = (
                flow.sum(self.square_op(x), self.axis, self.keepdim) / self.reduce_count
            )
            square = self.square_op(
                flow.sum(x, self.axis, self.keepdim) / self.reduce_count
            )
            subtract = self.subtract_op(sum, square)
            res = self.sqrt_op(subtract)
            return res


@register_tensor_op("std")
def std_op(tensor, dim, unbiased=False, keepdim=False):
    """
    Returns the standard-deviation of each row of the :attr:`input` tensor in the
    dimension :attr:`dim`. If :attr:`dim` is a list of dimensions,
    reduce over all of them.

    If keepdim is True, the output tensor is of the same size as input except in 
    the dimension(s) dim where it is of size 1. Otherwise, dim is squeezed, 
    resulting in the output tensor having 1 (or len(dim)) fewer dimension(s).

    If :attr:`unbiased` is ``False``, then the standard-deviation will be calculated
    via the biased estimator. Otherwise, Bessel's correction will be used.

    Args:
        input (Tensor): the input tensor.
        dim (int or tuple of python:ints): the dimension or dimensions to reduce.
        unbiased (bool): whether to use the unbiased estimation or not
        keepdim (bool): whether the output tensor has `dim` retained or not.

    For example:

    .. code-block:: python

        >>> import oneflow as flow
        >>> import numpy as np
        
        >>> arr = np.array([1.0, 2.0, 3.0])
        >>> input = flow.Tensor(arr)
        >>> output = flow.std(input, dim=0).numpy()
        >>> output
        array(0.8164968, dtype=float32)

    """
    return Std(dim, unbiased, keepdim)(tensor)


class Pow(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, y):
        if isinstance(y, (int, float)):
            return flow.F.pow_scalar(x, alpha=y)
        else:
            return flow.F.pow(x, y)


@register_tensor_op("pow")
def pow_op(tensor, exponent):
    """Takes the power of each element in input with exponent and returns a tensor with the result. Exponent can be either a single float number, a single int number, or a tensor with the same shape as input.
    When exponent is a scalar value, the operation applied is:

    .. math::
        \\text{out}_i = x_i ^ \\text{exponent}
\u200b
    When exponent is a tensor, the operation applied is:

    .. math::
        \\text{out}_i = x_i ^ {\\text{exponent}_i}

    Args:
        - input (Tensor): the input tensor.
        - exponent (int, float, Tensor): the exponent.

    Returns:
        Tensor: The result of variance on the specified axis of input Tensor

    For example:

    .. code-block:: python

        >>> import oneflow as flow
        >>> import numpy as np
        
        >>> x = flow.Tensor(np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0]))
        >>> out = flow.pow(x, 2).numpy()
        >>> out
        array([ 1.,  4.,  9., 16., 25., 36.], dtype=float32)

        >>> x = flow.Tensor(np.array([1.0, 2.0, 3.0, 4.0]))
        >>> y = flow.Tensor(np.array([1.0, 2.0, 3.0, 4.0]))
        >>> out = flow.pow(x, y).numpy()
        >>> out
        array([  1.,   4.,  27., 256.], dtype=float32)
        
    """
    return Pow()(tensor, exponent)


def addmm(x, mat1, mat2, alpha=1, beta=1):
    if len(x.shape) > 2 or len(mat1.shape) > 2 or len(mat2.shape) > 2:
        raise ValueError("input matrixes shape can not be greater than 2")
    else:
        return _mul(x, beta) + _mul(flow.F.matmul(mat1, mat2), alpha)


def addmm_op(input, mat1, mat2, alpha=1, beta=1):
    """addmm(beta=1, input, alpha=1, mat1, mat2, out=None) -> Tensor

    Performs a matrix multiplication of the matrices :attr:`mat1` and :attr:`mat2`.
    The matrix :attr:`input` is added to the final result.

    If :attr:`mat1` is a :math:`(n \\times m)` tensor, :attr:`mat2` is a
    :math:`(m \\times p)` tensor, then :attr:`input` must be
    broadcastable with a :math:`(n \\times p)` tensor
    and :attr:`out` will be a :math:`(n \\times p)` tensor.

    :attr:`alpha` and :attr:`beta` are scaling factors on matrix-vector product between
    :attr:`mat1` and :attr:`mat2` and the added matrix :attr:`input` respectively.

    .. math::
        \\text{out} = \\beta\\ \\text{input} + \\alpha\\ (\\text{mat1}_i \\mathbin{@} \\text{mat2}_i)

    For inputs of type `FloatTensor` or `DoubleTensor`, arguments :attr:`beta` and
    :attr:`alpha` must be real numbers, otherwise they should be integers.

    Args:
        beta (Number, optional): multiplier for :attr:`input` (:math:`\\beta`)
        input (Tensor): matrix to be added
        alpha (Number, optional): multiplier for :math:`mat1 @ mat2` (:math:`\\alpha`)
        mat1 (Tensor): the first matrix to be multiplied
        mat2 (Tensor): the second matrix to be multiplied
        out (Tensor, optional): the output tensor.

    For example:

        >>> import numpy as np
        >>> import oneflow as flow
        >>> input = flow.tensor(np.array([[1,2,4],[5,11,9.1]]))
        >>> mat1 = flow.tensor(np.array([[7.3,1.9,7.3],[10.2,1,5.5]])) 
        >>> mat2 = flow.tensor(np.array([[7.3,1.9,7.3],[10.2,1,5.5],[3.7,2.2,8.1]])) 
        >>> output = flow.addmm(input, mat1, mat2)
        >>> output
        tensor([[100.68,  33.83, 126.87],
                [110.01,  43.48, 133.61]], dtype=oneflow.float64)
        >>> output.shape
        flow.Size([2, 3])

        >>> input2 = flow.tensor(np.array([1.7]))
        >>> mat1 = flow.tensor(np.array([[1,2],[5,9.1],[7.7,1.4]]))
        >>> mat2 = flow.tensor(np.array([[1,2,3.7],[5,9.1,6.8]]))
        >>> output2 = flow.addmm(input2, mat1, mat2, alpha=1, beta=2)
        >>> output2
        tensor([[14.4 , 23.6 , 20.7 ],
                [53.9 , 96.21, 83.78],
                [18.1 , 31.54, 41.41]], dtype=oneflow.float64)
        >>> output2.shape
        flow.Size([3, 3])
    """
    return addmm(input, mat1, mat2, alpha, beta)


@register_tensor_op("addmm")
def addmm_op_tensor(input, mat1, mat2, alpha=1, beta=1):
    """
    See :func:`oneflow.addmm`
    """
    return addmm(input, mat1, mat2, alpha, beta)


class Clamp(Module):
    def __init__(self, min_value=None, max_value=None) -> None:
        super().__init__()
        if min_value is not None:
            floating_min_value = float(min_value)
            integral_min_value = int(min_value)
        if max_value is not None:
            floating_max_value = float(max_value)
            integral_max_value = int(max_value)
        if min_value is not None and max_value is not None:
            self._op = (
                flow.builtin_op("clip_by_scalar")
                .Input("x")
                .Output("y")
                .Attr("floating_min", floating_min_value)
                .Attr("integral_min", integral_min_value)
                .Attr("floating_max", floating_max_value)
                .Attr("integral_max", integral_max_value)
                .Build()
            )
        elif min_value is not None:
            self._op = (
                flow.builtin_op("clip_by_scalar_min")
                .Input("x")
                .Output("y")
                .Attr("floating_min", floating_min_value)
                .Attr("integral_min", integral_min_value)
                .Build()
            )
        elif max_value is not None:
            self._op = (
                flow.builtin_op("clip_by_scalar_max")
                .Input("x")
                .Output("y")
                .Attr("floating_max", floating_max_value)
                .Attr("integral_max", integral_max_value)
                .Build()
            )
        else:
            raise ValueError("min_value and max_value cannot be None at the same time")

    def forward(self, x):
        return self._op(x)[0]


def clamp_op(tensor, min=None, max=None):
    """
    Clamp all elements in :attr:`input` into the range `[` :attr:`min`, :attr:`max` `]` and return
    a resulting tensor:

    .. math::
        y_i = \\begin{cases}
            \\text{min} & \\text{if } x_i < \\text{min} \\\\
            x_i & \\text{if } \\text{min} \\leq x_i \\leq \\text{max} \\\\
            \\text{max} & \\text{if } x_i > \\text{max}
        \\end{cases}

    If :attr:`input` is of type `FloatTensor` or `DoubleTensor`, args :attr:`min`
    and :attr:`max` must be real numbers, otherwise they should be integers.

    Args:
        input (Tensor): the input tensor.
        min (Number): lower-bound of the range to be clamped to. Defaults to None.
        max (Number): upper-bound of the range to be clamped to. Defaults to None.
        out (Tensor, optional): the output tensor.

    For example:


    .. code-block:: python

        >>> import oneflow as flow
        >>> import numpy as np
        >>> arr = np.array([0.2, 0.6, -1.5, -0.3])
        >>> input = flow.Tensor(arr)
        >>> output = flow.clamp(input, min=-0.5, max=0.5)
        >>> output
        tensor([ 0.2,  0.5, -0.5, -0.3], dtype=oneflow.float32)

        >>> arr = np.array([0.2, 0.6, -1.5, -0.3])
        >>> input = flow.Tensor(arr)
        >>> output = flow.clamp(input, min=None, max=0.5)
        >>> output
        tensor([ 0.2,  0.5, -1.5, -0.3], dtype=oneflow.float32)

        >>> arr = np.array([0.2, 0.6, -1.5, -0.3])
        >>> input = flow.Tensor(arr)
        >>> output = flow.clamp(input, min=-0.5, max=None)
        >>> output
        tensor([ 0.2,  0.6, -0.5, -0.3], dtype=oneflow.float32)

    """
    return Clamp(min, max)(tensor)


@register_tensor_op("clamp")
def clamp_op_tensor(tensor, min=None, max=None):
    """
    See :func:`oneflow.clamp`
    """
    return Clamp(min, max)(tensor)


def clip_op(tensor, min=None, max=None):
    """
    Alias for :func:`oneflow.clamp`
    """
    return Clamp(min, max)(tensor)


@register_tensor_op("clip")
def clip_op_tensor(tensor, min=None, max=None):
    """
    See :func:`oneflow.clamp`
    """
    return Clamp(min, max)(tensor)


class Cosh(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x):
        return flow.F.cosh(x)


@register_tensor_op("cosh")
def cosh_op(tensor):
    """
    Returns a new tensor with the hyperbolic cosine of the elements of :attr:`input`.

    .. math::
        \\text{out}_{i} = \\cosh(\\text{input}_{i})

    Args:
        input (Tensor): the input tensor.

    For example:

    .. code-block:: python

        >>> import numpy as np
        >>> import oneflow as flow
        
        >>> arr = np.array([ 0.1632,  1.1835, -0.6979, -0.7325])
        >>> input = flow.Tensor(arr, dtype=flow.float32)
        >>> output = flow.cosh(input).numpy()
        >>> output
        array([1.0133467, 1.7859949, 1.2535787, 1.2804903], dtype=float32)

    """
    return Cosh()(tensor)


class Erf(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, input):
        return flow.F.erf(input)


@register_tensor_op("erf")
def erf_op(input):
    """Computes the error function of each element. The error function is defined as follows:

    .. math::
            \\operatorname{erf}(x)=\\frac{2}{\\sqrt{\\pi}} \\int_{0}^{x} e^{-t^{2}} d t

    Args:
        x (oneflow.Tensor): A Tensor

    Returns:
        oneflow.Tensor: The result Tensor   
               
    For example:

    .. code-block:: python

        >>> import oneflow as flow
        >>> import numpy as np
        
        >>> x = flow.Tensor(np.array([0, -1., 10.]), dtype=flow.float32)
        >>> out = flow.erf(x)
        >>> out.shape
        flow.Size([3])
        >>> out.numpy()
        array([ 0.       , -0.8427008,  1.       ], dtype=float32)

        >>> x = flow.Tensor(np.array([[0, -1., 10.], [5, 7, 0.8]]), dtype=flow.float32)
        >>> out = flow.erf(x)
        >>> out.shape
        flow.Size([2, 3])
        >>> out.numpy()
        array([[ 0.        , -0.8427008 ,  1.        ],
               [ 1.        ,  1.        ,  0.74210095]], dtype=float32)

        >>> x = flow.Tensor(np.array([[0, -1., 10.], [5, 7, 0.8], [2, 3, 4]]), dtype=flow.float32)
        >>> out = x.erf()
        >>> out.shape
        flow.Size([3, 3])
        >>> out.numpy()
        array([[ 0.        , -0.8427008 ,  1.        ],
               [ 1.        ,  1.        ,  0.74210095],
               [ 0.9953223 ,  0.9999779 ,  1.        ]], dtype=float32)

    """
    return Erf()(input)


@register_tensor_op("erf")
def erf_op_tensor(input):
    """
    See :func:`oneflow.erf`
    """
    return Erf()(input)


class Erfc(Module):
    def __init__(self) -> None:
        super().__init__()
        self.erfc_op = flow.builtin_op("erfc").Input("x").Output("y").Build()

    def forward(self, input):
        return self.erfc_op(input)[0]


@register_tensor_op("erfc")
def erfc_op(input):
    """Computes the complementary error function of each element of input. The complementary error 
    function is defined as follows:

    .. math::
            \\operatorname{erfc}(x)=1-\\frac{2}{\\sqrt{\\pi}} \\int_{0}^{x} e^{-t^{2}} d t

    Args:
        x (oneflow.Tensor): A Tensor

    Returns:
        oneflow.Tensor: The result Tensor

    For example:

    .. code-block:: python

        >>> import oneflow as flow
        >>> import numpy as np
        
        >>> x = flow.Tensor(np.array([0, -1., 10.]), dtype=flow.float32)
        >>> out = flow.erfc(x)
        >>> out.shape
        flow.Size([3])
        >>> out.numpy()
        array([1.0000000e+00, 1.8427007e+00, 2.8025969e-45], dtype=float32)

        >>> x = flow.Tensor(np.array([[0, -1., 10.], [5, 7, 0.8]]), dtype=flow.float32)
        >>> out = flow.erfc(x)
        >>> out.shape
        flow.Size([2, 3])
        >>> out.numpy()
        array([[1.0000000e+00, 1.8427007e+00, 2.8025969e-45],
               [1.5374597e-12, 4.1838257e-23, 2.5789905e-01]], dtype=float32)

        >>> x = flow.Tensor(np.array([[0, -1., 10.], [5, 7, 0.8], [2, 3, 4]]), dtype=flow.float32)
        >>> out = x.erfc()
        >>> out.shape
        flow.Size([3, 3])
        >>> out.numpy()
        array([[1.0000000e+00, 1.8427007e+00, 2.8025969e-45],
               [1.5374597e-12, 4.1838257e-23, 2.5789905e-01],
               [4.6777348e-03, 2.2090499e-05, 1.5417259e-08]], dtype=float32)
        
    """
    return Erfc()(input)


@register_tensor_op("erfc")
def erfc_op_tensor(input):
    """
    See :func:`oneflow.erfc`
    """
    return Erfc()(input)


class Ceil(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x):
        return flow.F.ceil(x)


def ceil_op(x):
    """Returns a new tensor with the ceil of the elements of :attr:`x`,
    the smallest integer greater than or equal to each element.

    The equation is: 

    .. math::
        \\text{out}_{i} = \\left\\lceil \\text{input}_{i} \\right\\rceil = \\left\\lfloor \\text{input}_{i} \\right\\rfloor + 1

    Args:
        x (oneflow.Tensor): A Tensor.
    
    Returns:
        oneflow.Tensor: The result Tensor

    For example: 


    .. code-block:: python 
        
        >>> import oneflow as flow
        >>> import numpy as np   
        >>> x = flow.Tensor(np.array([0.1, -2, 3.4]).astype(np.float32))
        >>> y = flow.ceil(x)
        >>> print(y.shape)
        flow.Size([3])
        >>> print(y.numpy())
        [ 1. -2.  4.]


        >>> x = flow.Tensor(np.array([[2.5, 4.6, 0.6],[7.8, 8.3, 9.2]]).astype(np.float32))
        >>> y = x.ceil()
        >>> print(y.shape)
        flow.Size([2, 3])
        >>> print(y.numpy())
        [[ 3.  5.  1.]
         [ 8.  9. 10.]]




        >>> x = flow.Tensor(np.array([[[2.2, 4.4, 6.5],[7.1, 8.2, 9.3]],[[10.6,11.2,12.2],[13.5,14.8,15.9]]]).astype(np.float32))
        >>> y = flow.ceil(x)
        >>> print(y.shape)
        flow.Size([2, 2, 3])
        >>> print(y.numpy())
        [[[ 3.  5.  7.]
          [ 8.  9. 10.]]
        <BLANKLINE>
         [[11. 12. 13.]
          [14. 15. 16.]]]

    """
    return Ceil()(x)


@register_tensor_op("ceil")
def ceil_op_tensor(x):
    """
    See :func:`oneflow.ceil`
    """
    return Ceil()(x)


class Expm1(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x):
        return flow.F.expm1(x)


def expm1_op(x):
    """Returns a new tensor with the exponential of the elements minus 1
    of :attr:`x`.


    The equation is: 

    .. math::
        y_{i} = e^{x_{i}} - 1

    Args:
        x (oneflow.Tensor): A Tensor.
    
    Returns:
        oneflow.Tensor: The result Tensor

    For example: 

    .. code-block:: python 
        
        >>> import oneflow as flow
        >>> import numpy as np
        >>> x = flow.Tensor(np.array([1, 2, 3]).astype(np.float32))
        >>> y = flow.expm1(x)
        >>> y.shape
        flow.Size([3])
        >>> y
        tensor([ 1.7183,  6.3891, 19.0855], dtype=oneflow.float32)


        >>> x = flow.Tensor(np.array([[2, 4, 6],[7, 8, 9]]).astype(np.float32))
        >>> y = x.expm1()
        >>> y.shape
        flow.Size([2, 3])
        >>> y
        tensor([[6.3891e+00, 5.3598e+01, 4.0243e+02],
                [1.0956e+03, 2.9800e+03, 8.1021e+03]], dtype=oneflow.float32)



        >>> x = flow.Tensor(np.array([[[2, 4, 6],[7, 8, 9]],[[10,11,12],[13,14,15]]]).astype(np.float32))
        >>> y = flow.expm1(x)
        >>> print(y.shape)
        flow.Size([2, 2, 3])
        >>> print(y.numpy())
        [[[6.3890562e+00 5.3598152e+01 4.0242880e+02]
          [1.0956332e+03 2.9799580e+03 8.1020840e+03]]
        <BLANKLINE>
         [[2.2025465e+04 5.9873141e+04 1.6275380e+05]
          [4.4241238e+05 1.2026032e+06 3.2690165e+06]]]


    """
    return Expm1()(x)


@register_tensor_op("expm1")
def expm1_op_tensor(x):
    """
    See :func:`oneflow.expm1`
    """
    return Expm1()(x)


class Topk(Module):
    def __init__(
        self, k, dim: int = None, largest: bool = True, sorted: bool = True
    ) -> None:
        super().__init__()
        self._op_topk_last_dim = (
            flow.builtin_op("top_k")
            .Input("in")
            .Output("out")
            .Attr("k", k)
            .Attr("sorted", sorted)
            .Build()
        )
        self.dim = dim
        self.largest = largest

    def forward(self, input):
        if self.dim == None:
            self.dim = -1
        num_axes = len(input.shape)
        axis = self.dim if self.dim >= 0 else self.dim + num_axes
        assert 0 <= axis < num_axes, "axis out of range"
        if axis == num_axes - 1:
            if self.largest:
                indices = self._op_topk_last_dim(input)[0]
            else:
                neg_input = flow.mul(input, -1)
                indices = self._op_topk_last_dim(neg_input)[0]
            return (flow.gather(input, indices, dim=axis), indices)
        else:
            perm = get_perm_when_transpose_axis_to_last_dim(num_axes, axis)
            x = flow.F.transpose(input, perm=perm)
            if self.largest:
                indices = self._op_topk_last_dim(x)[0]
            else:
                neg_input = flow.mul(x, -1)
                indices = self._op_topk_last_dim(neg_input)[0]
            indices = flow.F.transpose(indices, perm=get_inversed_perm(perm))
            return (flow.gather(input, indices, dim=axis), indices)


@register_tensor_op("topk")
def topk_op(input, k, dim: int = None, largest: bool = True, sorted: bool = True):
    """Finds the values and indices of the k largest entries at specified axis.

    Args:
        input (oneflow.Tensor): Input Tensor
        dim (int, optional): the dimension to sort along. Defaults to the last dim (-1)
        largest (bool, optional): controls whether to return largest or smallest elements
        sorted (bool, optional): controls whether to return the elements in sorted order

    Returns:
        Tuple(oneflow.Tensor, oneflow.Tensor(dtype=int32)): A tuple of (values, indices), where
        the indices are the indices of the elements in the original input tensor.

    For example:

    .. code-block:: python

        >>> import oneflow as flow
        >>> import numpy as np
        >>> x = np.array([[1, 3, 8, 7, 2], [1, 9, 4, 3, 2]], dtype=np.float32)
        >>> (values, indices) = flow.topk(flow.Tensor(x), k=3, dim=1)
        >>> values
        tensor([[8., 7., 3.],
                [9., 4., 3.]], dtype=oneflow.float32)
        >>> indices
        tensor([[2, 3, 1],
                [1, 2, 3]], dtype=oneflow.int32)
        >>> values.shape
        flow.Size([2, 3])
        >>> indices.shape
        flow.Size([2, 3])
        >>> (values, indices) = flow.topk(flow.Tensor(x), k=2, dim=1, largest=False)
        >>> values
        tensor([[1., 2.],
                [1., 2.]], dtype=oneflow.float32)
        >>> indices
        tensor([[0, 4],
                [0, 4]], dtype=oneflow.int32)
        >>> values.shape
        flow.Size([2, 2])
        >>> indices.shape
        flow.Size([2, 2])

    """
    return Topk(k=k, dim=dim, largest=largest, sorted=sorted)(input)


class ElementwiseMinimum(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, y):
        return flow.F.elementwise_min(x, y)


class BroadcastMinimum(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, y):
        return flow.F.broadcast_min(x, y)


@register_tensor_op("minimum")
def minimum(x, y):
    r"""Computes the element-wise minimum of x and y.

    For example:

    .. code-block:: python

        >>> import numpy as np
        >>> import oneflow as flow

        >>> x = flow.tensor((1, 2, -1), dtype=flow.float)
        >>> y = flow.tensor((3, 0, 4), dtype=flow.float)
        >>> flow.minimum(x, y)
        tensor([ 1.,  0., -1.], dtype=oneflow.float32)

        >>> x = flow.tensor((1,), dtype=flow.float)
        >>> y = flow.tensor((3, 0, 4), dtype=flow.float)
        >>> flow.minimum(x, y)
        tensor([1., 0., 1.], dtype=oneflow.float32)
    """
    if x.shape == y.shape:
        return ElementwiseMinimum()(x, y)
    else:
        return BroadcastMinimum()(x, y)


class ElementwiseMaximum(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, y):
        return flow.F.elementwise_max(x, y)


class BroadcastMaximum(Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, x, y):
        return flow.F.broadcast_max(x, y)


@register_tensor_op("maximum")
def maximum(x, y):
    r"""Computes the element-wise maximum of x and y.

    For example:

    .. code-block:: python

        >>> import numpy as np
        >>> import oneflow as flow

        >>> x = flow.tensor((1, 2, -1), dtype=flow.float)
        >>> y = flow.tensor((3, 0, 4), dtype=flow.float)
        >>> flow.maximum(x, y)
        tensor([3., 2., 4.], dtype=oneflow.float32)

        >>> x = flow.tensor((1,), dtype=flow.float)
        >>> y = flow.tensor((3, 0, 4), dtype=flow.float)
        >>> flow.maximum(x, y)
        tensor([3., 1., 4.], dtype=oneflow.float32)
    """
    if x.shape == y.shape:
        return ElementwiseMaximum()(x, y)
    else:
        return BroadcastMaximum()(x, y)


if __name__ == "__main__":
    import doctest

    doctest.testmod(raise_on_error=True)

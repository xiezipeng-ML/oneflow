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
from oneflow.nn.module import Module


class FakeQuantization(Module):
    def __init__(
        self,
        quantization_formula: str = "google",
        quantization_bit: int = 8,
        quantization_scheme: str = "symmetric",
    ) -> None:
        super().__init__()
        self.quantization_formula = quantization_formula
        self.quantization_bit = quantization_bit
        self.quantization_scheme = quantization_scheme

    def forward(self, input, scale, zero_point):
        return flow.F.fake_quantization(
            input,
            scale,
            zero_point,
            self.quantization_formula,
            self.quantization_bit,
            self.quantization_scheme,
        )


def fake_quantization_op(
    input,
    scale,
    zero_point,
    quantization_formula: str = "google",
    quantization_bit: int = 8,
    quantization_scheme: str = "symmetric",
):
    """Simulate the quantize and dequantize operations in training time.

    The output will be computed as:

        if quantization_scheme == "symmetric":

        .. math::

            & quant\\_max = 2^{quantization\\_to\\_bit - 1} - 1

            & quant\\_min = -quant\\_max

            & clamp(round(x / scale), quant\\_min, quant\\_max) * scale

        elif quantization_scheme == "affine":

        .. math::

            & quant\\_max = 2^{quantization\\_to\\_bit} - 1

            & quant\\_min = 0

            & (clamp(round(x / scale + zero\\_point), quant\\_min, quant\\_max) - zero\\_point) * scale

    Args:
        input (oneflow.Tensor): input tensor.
        scale (oneflow.Tensor): Computed by min_max_observer or moving_average_min_max_observer op.
        zero_point (oneflow.Tensor): Computed by min_max_observer or moving_average_min_max_observer op.
        quantization_bit (int): Quantize input to uintX / intX, X can be in range [2, 8]. Defaults to 8.
        quantization_scheme (str): "symmetric" or "affine", quantize to signed / unsigned integer. Defaults to "symmetric".
        quantization_formula (str): Support "google" or "cambricon".

    Returns:
        oneflow.Tensor: Input tensor after quantize and dequantize operations.

    For example:

    .. code-block:: python

    """
    return FakeQuantization(
        quantization_formula=quantization_formula,
        quantization_bit=quantization_bit,
        quantization_scheme=quantization_scheme,
    )(input, scale, zero_point)


if __name__ == "__main__":
    import doctest

    doctest.testmod(raise_on_error=True)

import oneflow as flow
import numpy as np
import oneflow.typing as tp
from test_util import GenArgList
import unittest
from collections import OrderedDict
import os


def _compare_selu_with_np(input_shape, device_type, value_type, machine_ids, device_counts
):
    scale = 1.0507009873554804934193349852946
    alpha = 1.6732632423543772848170429916717

    if value_type[1] == flow.float16:
        input_1 = np.random.uniform(-1, 1, size=input_shape).astype(np.float16)
        input_1 = np.array(input_1, dtype=value_type[0])
        scale = np.array(scale).astype(np.float16).astype(value_type[0])
        alpha = np.array(alpha).astype(np.float16).astype(value_type[0])
    else:
        input_1 = np.random.uniform(-1, 1, size=input_shape).astype(value_type[0])

    assert device_type in ["cpu", "gpu"]

    flow.clear_default_session()
    if device_type == "cpu":
        flow.config.cpu_device_num(device_counts)
    else:
        flow.config.gpu_device_num(device_counts)

    func_config = flow.FunctionConfig()
    func_config.default_placement_scope(flow.scope.placement(device_type, machine_ids))

    if value_type[1] == flow.float16:
        func_config.default_data_type(flow.float32)
    else:
        func_config.default_data_type(value_type[1])

    def np_selu(input, scale, alpha):
        elem_cnt = input.size
        init_shape = input.shape
        input = input.flatten()
        out = np.zeros_like(input)

        for i in range(elem_cnt):
            if input[i] > 0:
                out[i] = scale * input[i]
            else:
                out[i] = scale * alpha * (np.exp(input[i]) - 1)

        out = np.reshape(out, init_shape)
        if value_type[1] == flow.float16:
            return np.array(out).astype(np.float16).astype(value_type[0])

        else:
            return np.array(out).astype(value_type[0])

    np_out_selu = np_selu(input_1, scale, alpha)

    def np_diff(input, scale, alpha):
        input_shape = input.shape
        input = input.flatten()
        elem_cnt = input.size
        diff = np.zeros(shape=(elem_cnt,))
        for i in range(elem_cnt):
            if input[i] > 0:
                diff[i] = scale * 1
            else:
                diff[i] = scale * alpha * np.exp(input[i])
        diff = np.reshape(diff, newshape=input_shape)
        if value_type[1] == flow.float16:
            diff = np.array(diff, dtype=np.float16).astype(value_type[0])
        else:
            diff = np.array(diff, dtype=value_type[0])
        return diff

    _np_grad = np_diff(input_1, scale, alpha)

    def assert_prediction_grad(blob: tp.Numpy):
        if value_type[1] == flow.float16:
            assert np.allclose(blob, _np_grad, atol=1e-3)
        else:
            assert np.allclose(blob, _np_grad, atol=1e-5)

    if value_type[1] == flow.float16:

        @flow.global_function(
            type="train", function_config=func_config,
        )
        def oneflow_selu(
            of_input_1: tp.Numpy.Placeholder(shape=input_1.shape, dtype=flow.float32),
        ) -> tp.Numpy:
            with flow.scope.placement(device_type, "0:0"):
                v = flow.get_variable(
                    shape=input_1.shape,
                    dtype=flow.float32,
                    initializer=flow.zeros_initializer(),
                    name="x_var",
                )
                x_var = of_input_1 + v
                x_f16 = flow.cast(x_var, flow.float16)

            of_selu_out_f16 = flow.nn.selu(x_f16)
            of_selu_out_f32 = flow.cast(of_selu_out_f16, flow.float32)

            with flow.scope.placement(device_type, "0:0"):
                flow.optimizer.SGD(
                    flow.optimizer.PiecewiseConstantScheduler([], [1e-3]), momentum=0
                ).minimize(of_selu_out_f32)

            flow.watch_diff(x_var, assert_prediction_grad)

            return of_selu_out_f32

    elif value_type[1] == flow.float32 or value_type[1] == flow.float64:

        @flow.global_function(
            type="train", function_config=func_config,
        )
        def oneflow_selu(
            of_input_1: tp.Numpy.Placeholder(shape=input_1.shape, dtype=value_type[1]),
        ) -> tp.Numpy:
            with flow.scope.placement(device_type, "0:0"):
                v = flow.get_variable(
                    shape=input_1.shape,
                    dtype=value_type[1],
                    initializer=flow.zeros_initializer(),
                    name="x_var",
                )
                x_var = of_input_1 + v

            flow.watch_diff(x_var, assert_prediction_grad)

            of_selu_out = flow.nn.selu(x_var)

            with flow.scope.placement(device_type, "0:0"):
                flow.optimizer.SGD(
                    flow.optimizer.PiecewiseConstantScheduler([], [1e-3]), momentum=0
                ).minimize(of_selu_out)

            return of_selu_out

    of_out_selu = oneflow_selu(input_1)

    if value_type[1] == flow.float16:
        assert np.allclose(of_out_selu, np_out_selu, atol=1e-3)
    else:
        assert np.allclose(of_out_selu, np_out_selu, atol=1e-5)


def _gen_arg_dict(
    shape, device_type, value_type, machine_ids, device_counts
):
    # Generate a dict to pass parameter to test case
    arg_dict = OrderedDict()
    arg_dict["input_shape"] = [shape]
    arg_dict["device_type"] = [device_type]
    if value_type == "float" and device_type == "cpu":
        arg_dict["value_type"] = [
            (np.float32, flow.float32),
            (np.float64, flow.float64),
        ]
    else:
        arg_dict["value_type"] = [
            (np.float32, flow.float16),
            (np.float32, flow.float32),
            (np.float64, flow.float64),
        ]
    arg_dict["machine_ids"] = [machine_ids]
    arg_dict["device_counts"] = [device_counts]
    return arg_dict


@flow.unittest.skip_unless_1n1d()
class Testselu1n1d(flow.unittest.TestCase):
    def test_selu_cpu(test_case):
        arg_dict = _gen_arg_dict(
            shape=(3, 3),
            device_type="cpu",
            value_type="float",
            machine_ids="0:0",
            device_counts=1,
        )
        for arg in GenArgList(arg_dict):
            _compare_selu_with_np(*arg)

    @unittest.skipIf(os.getenv("ONEFLOW_TEST_CPU_ONLY"), "only test cpu cases")
    def test_selu_gpu(test_case):
        arg_dict = _gen_arg_dict(
            shape=(4, 4),
            device_type="gpu",
            value_type="float",
            machine_ids="0:0",
            device_counts=1,
        )
        for arg in GenArgList(arg_dict):
            _compare_selu_with_np(*arg)


@flow.unittest.skip_unless_1n2d()
class Testselu1n2d(flow.unittest.TestCase):
    @unittest.skipIf(os.getenv("ONEFLOW_TEST_CPU_ONLY"), "only test cpu cases")
    def test_selu_gpu_1n2d(test_case):
        arg_dict = _gen_arg_dict(
            shape=(4, 8, 4),
            device_type="gpu",
            value_type="float",
            machine_ids="0:0-1",
            device_counts=2,
        )
        for arg in GenArgList(arg_dict):
            _compare_selu_with_np(*arg)


if __name__ == "__main__":
    unittest.main()
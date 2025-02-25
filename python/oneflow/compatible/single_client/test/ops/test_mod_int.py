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

import unittest

import numpy as np

import oneflow.compatible.single_client.unittest
from oneflow.compatible import single_client as flow
from oneflow.compatible.single_client import typing as oft

func_config = flow.FunctionConfig()
func_config.default_data_type(flow.int32)


def GenerateTest(test_case, a_shape, b_shape):
    @flow.global_function(function_config=func_config)
    def ModJob(
        a: oft.Numpy.Placeholder(a_shape, dtype=flow.int32),
        b: oft.Numpy.Placeholder(b_shape, dtype=flow.int32),
    ):
        return a % b

    a = (np.random.rand(*a_shape) * 1000).astype(np.int32) + 1
    b = (np.random.rand(*b_shape) * 1000).astype(np.int32) + 1
    y = ModJob(a, b).get().numpy()
    test_case.assertTrue(np.array_equal(y, a % b))


@flow.unittest.skip_unless_1n1d()
class TestModInt(flow.unittest.TestCase):
    def test_naive(test_case):
        @flow.global_function(function_config=func_config)
        def ModJob(
            a: oft.Numpy.Placeholder((5, 2), dtype=flow.int32),
            b: oft.Numpy.Placeholder((5, 2), dtype=flow.int32),
        ):
            return a % b

        x = (np.random.rand(5, 2) * 1000).astype(np.int32) + 1
        y = (np.random.rand(5, 2) * 1000).astype(np.int32) + 1
        z = None
        z = ModJob(x, y).get().numpy()
        test_case.assertTrue(np.array_equal(z, x % y))

    def test_broadcast(test_case):
        @flow.global_function(function_config=func_config)
        def ModJob(
            a: oft.Numpy.Placeholder((5, 2), dtype=flow.int32),
            b: oft.Numpy.Placeholder((1, 2), dtype=flow.int32),
        ):
            return a % b

        x = (np.random.rand(5, 2) * 1000).astype(np.int32) + 1
        y = (np.random.rand(1, 2) * 1000).astype(np.int32) + 1
        z = None
        z = ModJob(x, y).get().numpy()
        test_case.assertTrue(np.array_equal(z, x % y))

    def test_xy_mod_x1(test_case):
        GenerateTest(test_case, (64, 64), (64, 1))

    def test_xy_mod_1y(test_case):
        GenerateTest(test_case, (64, 64), (1, 64))

    def test_xyz_mod_x1z(test_case):
        GenerateTest(test_case, (64, 64, 64), (64, 1, 64))

    def test_xyz_mod_1y1(test_case):
        GenerateTest(test_case, (64, 64, 64), (1, 64, 1))


if __name__ == "__main__":
    unittest.main()

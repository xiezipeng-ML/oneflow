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
import oneflow as flow
from oneflow.distributed.ddp import ddp
import oneflow.unittest

import numpy as np


@flow.unittest.skip_unless_1n2d()
class TestDDP(flow.unittest.TestCase):
    def test_ddp_basic(test_case):
        class Mul(flow.nn.Module):
            def __init__(self):
                super().__init__()
                self.w = flow.nn.Parameter(flow.Tensor([1]))

            def forward(self, x):
                return x * self.w

        rank = flow.framework.distribute.get_rank()
        if rank == 0:
            x = flow.Tensor([1])
        elif rank == 1:
            x = flow.Tensor([2])
        else:
            raise ValueError()

        x = x.to("cuda")
        m = Mul().to("cuda")
        m = ddp(m)
        y = m(x)
        y.backward()

        test_case.assertTrue(np.allclose(m.w.grad.numpy(), np.array([3])))

    def test_ddp_with_unused_param(test_case):
        class Model(flow.nn.Module):
            def __init__(self):
                super().__init__()
                self.w = flow.nn.Parameter(flow.Tensor([1]))
                self.used_only_in_rank0 = flow.nn.Parameter(flow.Tensor([2]))
                self.unused_in_all_ranks = flow.nn.Parameter(flow.Tensor([3]))

            def forward(self, x):
                x = x * self.w
                if flow.framework.distribute.get_rank() == 0:
                    x = x * self.used_only_in_rank0
                return x

        rank = flow.framework.distribute.get_rank()
        if rank == 0:
            x = flow.Tensor([1])
        elif rank == 1:
            x = flow.Tensor([2])
        else:
            raise ValueError()

        x = x.to("cuda")
        m = Model().to("cuda")
        m = ddp(m)
        y = m(x)
        y.backward()

        test_case.assertTrue(np.allclose(m.w.grad.numpy(), np.array([4])))
        test_case.assertTrue(np.allclose(m.used_only_in_rank0.grad.numpy(), np.array([1])))
        test_case.assertTrue(np.allclose(m.unused_in_all_ranks.grad.numpy(), np.array([0])))

    def test_out_of_order_execution(test_case):
        class Model(flow.nn.Module):
            def __init__(self):
                super().__init__()
                self.w1 = flow.nn.Parameter(flow.Tensor([1]))
                self.w2 = flow.nn.Parameter(flow.Tensor([2]))
                self.w3 = flow.nn.Parameter(flow.Tensor([3]))

            def forward(self, x):
                if flow.framework.distribute.get_rank() == 0:
                    x *= self.w1
                    x *= self.w2
                    x *= self.w3
                else:
                    x *= self.w3
                    x *= self.w2
                    x *= self.w1
                return x

        rank = flow.framework.distribute.get_rank()
        if rank == 0:
            x = flow.Tensor([1])
        elif rank == 1:
            x = flow.Tensor([2])
        else:
            raise ValueError()

        x = x.to("cuda")
        m = Model().to("cuda")
        m = ddp(m)
        y = m(x)
        y.backward()

        test_case.assertTrue(np.allclose(m.w1.grad.numpy(), np.array([18])))
        test_case.assertTrue(np.allclose(m.w2.grad.numpy(), np.array([9])))
        test_case.assertTrue(np.allclose(m.w3.grad.numpy(), np.array([6])))


if __name__ == "__main__":
    unittest.main()
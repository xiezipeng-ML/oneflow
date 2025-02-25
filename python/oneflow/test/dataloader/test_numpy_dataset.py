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

import oneflow as flow
import oneflow.unittest
import oneflow.utils.data as data


class ScpDataset(flow.utils.data.Dataset):
    def __init__(self, chunksize=200, dim=81, length=2000):
        self.chunksize = chunksize
        self.dim = dim
        self.length = length

    def __getitem__(self, index):
        np.random.seed(index)
        return np.random.randn(self.chunksize, self.dim)

    def __len__(self):
        return self.length


@flow.unittest.skip_unless_1n1d()
class TestNumpyDataset(flow.unittest.TestCase):
    def test_numpy_dataset(test_case):
        dataset = ScpDataset()
        dataloader = data.DataLoader(dataset, batch_size=16, shuffle=True)
        for X in dataloader:
            test_case.assertEqual(X.shape, flow.Size([16, 200, 81]))


if __name__ == "__main__":
    unittest.main()

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

import cnns_tests
import env_2node
import numpy
from absl import app
from absl.testing import absltest
from test_2node_mixin import Test2NodeMixin

import oneflow as flow


class TestAlexNet(Test2NodeMixin, cnns_tests.TestAlexNetMixin, absltest.TestCase):
    pass


class TestResNet50(Test2NodeMixin, cnns_tests.TestResNet50Mixin, absltest.TestCase):
    pass


class TestVgg16(Test2NodeMixin, cnns_tests.TestVgg16Mixin, absltest.TestCase):
    pass


class TestInceptionV3(
    Test2NodeMixin, cnns_tests.TestInceptionV3Mixin, absltest.TestCase
):
    pass


flow.unittest.register_test_cases(
    scope=globals(),
    directory=os.path.dirname(os.path.realpath(__file__)),
    filter_by_num_nodes=lambda x: x == 2,
    base_class=absltest.TestCase,
)


def main(argv):
    env_2node.Init()
    absltest.main()


if __name__ == "__main__":
    app.run(main)

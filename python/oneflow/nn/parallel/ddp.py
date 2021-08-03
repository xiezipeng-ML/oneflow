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
from collections import OrderedDict

import oneflow as flow
from oneflow.ops.builtin_ops import BuiltinOp as builtin_op
from oneflow.framework.tensor_tuple_util import convert_to_tensor_tuple


def allreducefn(ddp_state_for_reversed_params, param, allreduce_module):
    def allreduce(grad):
        ddp_state_for_reversed_params[param][0] = True
        ret = None
        for cur_param, (ready, deleted) in ddp_state_for_reversed_params.items():
            if deleted:
                continue
            if ready:
                ddp_state_for_reversed_params[cur_param][1] = True
                if cur_param == param:
                    ret = allreduce_module(grad)[0]
                else:
                    cur_param.grad = allreduce_module(cur_param.grad)[0]
            else:
                break
        return ret

    return allreduce


def DistributedDataParallel(module: "flow.nn.Module"):
    world_size = flow.framework.distribute.get_world_size()
    # assert single node
    assert flow.framework.distribute.get_local_rank() == flow.framework.distribute.get_rank()
    allreduce_module = flow.nn.AllReduce(f'device_tag: "gpu", device_name: "0:0-{world_size-1}"')
    ddp_state_for_reversed_params = OrderedDict(
        reversed([(x, [False, False]) for x in module.parameters()])
    )
    module._ddp_state_for_reversed_params = ddp_state_for_reversed_params
    for param in module.parameters():
        param.register_hook(lambda grad: grad / world_size)
        param.register_hook(allreducefn(ddp_state_for_reversed_params, param, allreduce_module))

    def hook(module, input, output):
        ddp_state_for_reversed_params = module._ddp_state_for_reversed_params
        for state in ddp_state_for_reversed_params.values():
            state[0], state[1] = False, False
        output = flow.F.select_first(
            convert_to_tensor_tuple([output, *ddp_state_for_reversed_params.keys()])
        )
        return output

    module.register_forward_hook(hook)
    return module


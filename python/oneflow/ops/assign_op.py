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

import oneflow
import oneflow.core.operator.op_conf_pb2 as op_conf_util
import oneflow.core.register.logical_blob_id_pb2 as logical_blob_id_util
import oneflow.eager.boxing_util as boxing_util
import oneflow.framework.hob as hob
import oneflow.framework.id_util as id_util
import oneflow.framework.interpret_util as interpret_util
import oneflow.framework.placement_context as placement_ctx
import oneflow.framework.remote_blob as remote_blob_util
import oneflow.support.enable_if as enable_if


def assign(ref, value, dtype=None, name=None):
    if name is None:
        name = id_util.UniqueStr("Assign_")
    op = (
        oneflow.consistent_user_op_builder(name)
        .Op("assign")
        .Input("ref", [ref])
        .Input("value", [value])
        .Build()
    )
    op.InferAndTryRun()


def api_system_assign(ref, value, validate_shape=None, use_locking=None, name=None):
    api = enable_if.unique([lazy_system_assign, eager_system_assign])
    return api(
        ref, value, validate_shape=validate_shape, use_locking=use_locking, name=name
    )


@enable_if.condition(hob.in_global_mode & ~hob.eager_execution_enabled)
def lazy_system_assign(ref, value, validate_shape=None, use_locking=None, name=None):
    op_conf = _SystemAssignOpConf(ref, value, name=name)
    (
        device_tag,
        machine_device_ids,
        hierarchy,
    ) = oneflow._oneflow_internal.GetDeviceTagAndMachineDeviceIdsAndHierarchy(
        ref.parallel_conf
    )
    if hierarchy is not None:
        hierarchy = tuple(hierarchy.dim())
    with oneflow.scope.placement(device_tag, machine_device_ids, hierarchy):
        interpret_util.Forward(op_conf)
    return ref


@enable_if.condition(hob.in_global_mode & hob.eager_execution_enabled)
def eager_system_assign(ref, value, validate_shape=None, use_locking=None, name=None):
    op_conf = _SystemAssignOpConf(ref, value, name=name)
    oneflow._oneflow_internal.deprecated.LogicalRun(
        lambda builder: boxing_util.BuildAssignInstruction(
            builder, ref.blob_object, value.blob_object, op_conf
        )
    )
    return ref


def api_one_to_one_assign(ref, value):
    assert hob.eager_execution_enabled(None)
    oneflow._oneflow_internal.deprecated.LogicalRun(
        lambda builder: builder.Build121AssignInstruction(
            ref.blob_object, value.blob_object
        )
    )
    return ref


def _SystemAssignOpConf(ref, value, name=None):
    if name is None:
        name = id_util.UniqueStr("Assign_")
    op_conf = op_conf_util.OperatorConf()
    op_conf.name = name
    op_conf.assign_conf.ref = ref.unique_name
    op_conf.assign_conf.value = value.unique_name
    return op_conf

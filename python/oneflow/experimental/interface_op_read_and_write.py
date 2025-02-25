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
import oneflow._oneflow_internal
import oneflow._oneflow_internal.oneflow.core.common.shape as shape_proto_cfg
import oneflow._oneflow_internal.oneflow.core.job.placement as placement_cfg
import oneflow._oneflow_internal.oneflow.core.register.logical_blob_id as lbi_util
import oneflow.core.register.logical_blob_id_pb2 as logical_blob_id_util
import oneflow.framework.dtype as dtype_util
import oneflow.framework.input_blob_def as input_blob_def_util
import oneflow.framework.push_util as push_util
import oneflow.framework.remote_blob as remote_blob_util
import oneflow.framework.runtime_mode as rt_mode
import oneflow.framework.session_context as session_ctx
import oneflow.support.async_util as async_util


def sync_default_session_if_normal():
    if rt_mode.CurrentMode() == rt_mode.NORMAL_MODE:
        flow.sync_default_session()
    else:
        pass


blob_register = oneflow._oneflow_internal.GetDefaultBlobRegister()


def _GetInterfaceBlobObject(builder, op_name):
    sess = session_ctx.GetDefaultSession()
    if oneflow._oneflow_internal.EagerExecutionEnabled():
        return sess.var_name2var_blob[op_name].blob_object
    sess = session_ctx.GetDefaultSession()
    op_attribute = sess.OpAttribute4InterfaceOpName(op_name)
    cfg_op_attribute = oneflow._oneflow_internal.deprecated.MakeOpAttributeByString(
        str(op_attribute)
    )
    parallel_conf = sess.ParallelConf4LazyInterfaceOpName(op_name)
    if not isinstance(
        parallel_conf, oneflow._oneflow_internal.oneflow.core.job.placement.ParallelConf
    ):
        parallel_conf_cfg = placement_cfg.ParallelConf()
        parallel_conf_cfg.set_device_tag(parallel_conf.device_tag)
        for device_name in parallel_conf.device_name:
            parallel_conf_cfg.add_device_name(device_name)
        if parallel_conf.HasField("hierarchy"):
            hierarchy = shape_proto_cfg.ShapeProto()
            for dim in parallel_conf.hierarchy.dim:
                hierarchy.add_dim(dim)
            assert hierarchy.dim_size() > 0
            parallel_conf_cfg.mutable_hierarchy().CopyFrom(hierarchy)
        parallel_conf = parallel_conf_cfg
    blob_object = builder.MakeLazyRefBlobObject(
        op_name, cfg_op_attribute, parallel_conf
    )
    return blob_object


def GetEagerInterfaceBlob(op_name):
    sync_default_session_if_normal()
    sess = session_ctx.GetDefaultSession()

    def CreateBlob():
        job_name = sess.JobName4InterfaceOpName(op_name)

        def Build(builder, Yield):
            blob_object = _GetInterfaceBlobObject(builder, op_name)
            lbi = lbi_util.LogicalBlobId()
            lbi.set_op_name(op_name)
            op_attribute = sess.OpAttribute4InterfaceOpName(op_name)
            assert len(op_attribute.output_bns) == 1
            lbi.set_blob_name(op_attribute.output_bns[0])
            if blob_object.op_arg_parallel_attr.is_mirrored():
                remote_blob = oneflow._oneflow_internal.EagerMirroredBlob(
                    lbi, blob_object, blob_register, job_name
                )
            else:
                remote_blob = oneflow._oneflow_internal.EagerConsistentBlob(
                    lbi, blob_object, blob_register, job_name
                )
            Yield(remote_blob)

        def AsyncGetInterfaceBlob(Yield):
            oneflow._oneflow_internal.deprecated.LogicalRun(
                lambda builder: Build(builder, Yield)
            )

        blob = async_util.Await(1, AsyncGetInterfaceBlob)[0]
        return blob

    return sess.FindOrCreateLazyBlob(op_name, CreateBlob)


def GetInterfaceBlobValue(op_name):
    sync_default_session_if_normal()
    sess = session_ctx.GetDefaultSession()
    job_name = sess.JobName4InterfaceOpName(op_name)

    def AsyncGetInterfaceBlobValue(Yield):
        def build(builder):
            blob_object = GetEagerInterfaceBlob(op_name).blob_object
            lbi = lbi_util.LogicalBlobId()
            lbi.set_op_name(op_name)
            op_attribute = sess.OpAttribute4InterfaceOpName(op_name)
            assert len(op_attribute.output_bns) == 1
            lbi.set_blob_name(op_attribute.output_bns[0])
            if not isinstance(lbi, lbi_util.LogicalBlobId):
                cfg_lbi = lbi_util.LogicalBlobId()
                cfg_lbi.set_op_name(lbi.op_name)
                cfg_lbi.set_blob_name(lbi.blob_name)
                lbi = cfg_lbi
            if blob_object.op_arg_parallel_attr.is_mirrored():
                remote_blob = oneflow._oneflow_internal.EagerMirroredBlob(
                    lbi, blob_object, blob_register, job_name
                )
            else:
                remote_blob = oneflow._oneflow_internal.EagerConsistentBlob(
                    lbi, blob_object, blob_register, job_name
                )
            value = remote_blob.numpy()
            Yield(value)

        oneflow._oneflow_internal.deprecated.LogicalRun(build)

    return async_util.Await(1, AsyncGetInterfaceBlobValue)[0]


def FeedValueToInterfaceBlobObject(blob_object, ndarray):
    sync_default_session_if_normal()

    def build(builder):
        if blob_object.op_arg_parallel_attr.is_mirrored():
            input_blob_def = input_blob_def_util.MirroredTensorDef(
                ndarray.shape,
                dtype=dtype_util.convert_numpy_dtype_to_oneflow_dtype(ndarray.dtype),
            )
        else:
            input_blob_def = input_blob_def_util.FixedTensorDef(
                ndarray.shape,
                dtype=dtype_util.convert_numpy_dtype_to_oneflow_dtype(ndarray.dtype),
            )
        push_util.FeedValueToEagerBlob(blob_object, input_blob_def, ndarray)

    oneflow._oneflow_internal.deprecated.LogicalRun(build)


def FeedValueToInterfaceBlob(op_name, ndarray):
    sync_default_session_if_normal()

    def AsyncFeedValueToInterfaceBlob(Yield):
        def build(builder):
            blob_object = GetEagerInterfaceBlob(op_name).blob_object
            FeedValueToInterfaceBlobObject(blob_object, ndarray)
            Yield()

        oneflow._oneflow_internal.deprecated.LogicalRun(build)

    async_util.Await(1, AsyncFeedValueToInterfaceBlob)

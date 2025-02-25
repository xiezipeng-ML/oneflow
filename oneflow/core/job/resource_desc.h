/*
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
*/
#ifndef ONEFLOW_CORE_JOB_RESOURCE_DESC_H_
#define ONEFLOW_CORE_JOB_RESOURCE_DESC_H_

#include <set>
#include "oneflow/core/job/job.pb.h"
#include "oneflow/core/job/resource.pb.h"
#include "oneflow/core/job/env_desc.h"

namespace oneflow {

static const size_t kMB = 1024 * 1024;

class ResourceDesc final {
 public:
  OF_DISALLOW_COPY_AND_MOVE(ResourceDesc);
  ResourceDesc(const Resource& resource, int64_t num_process_per_node);
  ResourceDesc(const Resource& resource)
      : resource_(resource) {}  // TODO(yaochi): Only for eager, remove it later

  ~ResourceDesc() = default;

  const std::set<int64_t>& process_ranks() const { return process_ranks_; }
  __attribute__((deprecated)) Machine machine(int32_t idx) const;
  size_t CommNetWorkerNum() const { return resource_.comm_net_worker_num(); }
  int32_t CpuDeviceNum() const { return resource_.cpu_device_num(); }
  int32_t GpuDeviceNum() const { return resource_.gpu_device_num(); }
  int32_t MemZoneNum() const { return GpuDeviceNum() + 1; }
  int32_t MaxMdSaveWorkerNum() const { return resource_.max_mdsave_worker_num(); }
  size_t reserved_host_mem_byte() const { return resource_.reserved_host_mem_mbyte() * kMB; }
  size_t reserved_device_mem_byte() const { return resource_.reserved_device_mem_mbyte() * kMB; }
  bool thread_enable_local_message_queue() const {
    return resource_.thread_enable_local_message_queue();
  }
  bool enable_thread_local_cache() const { return resource_.enable_thread_local_cache(); }
  size_t thread_local_cache_max_size() const { return resource_.thread_local_cache_max_size(); }
  int32_t ComputeThreadPoolSize() const;
  bool enable_debug_mode() const;
  bool enable_dry_run() const;
  CollectiveBoxingConf collective_boxing_conf() const;
  bool nccl_use_compute_stream() const;

  void SetMachineNum(int32_t val) { resource_.set_machine_num(val); }
  void SetCpuDeviceNum(int32_t val) { resource_.set_cpu_device_num(val); }
  bool enable_tensor_float_32_compute() const { return resource_.enable_tensor_float_32_compute(); }
  const Resource& resource() const { return resource_; }
  void DumpCudnnConf(const JobConfigProto& job_conf);

 private:
  Resource resource_;
  std::set<int64_t> process_ranks_;
};

}  // namespace oneflow

#endif  // ONEFLOW_CORE_JOB_RESOURCE_DESC_H_

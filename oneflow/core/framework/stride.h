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

#ifndef ONEFLOW_CORE_FRAMEWORK_STRIDE_H_
#define ONEFLOW_CORE_FRAMEWORK_STRIDE_H_

#include "oneflow/core/common/shape.h"
#include "oneflow/core/common/util.h"

namespace oneflow {

class Stride final {
 public:
  Stride() = default;
  explicit Stride(const Shape& shape);
  explicit Stride(const StrideVector& stride_vec) : stride_vec_(stride_vec) {}
  explicit Stride(StrideVector&& stride_vec) : stride_vec_(stride_vec) {}
  Stride(const std::initializer_list<int64_t>& stride_vec) : stride_vec_(stride_vec) {}
  Stride& operator=(const Stride& stride);
  ~Stride() = default;

  bool operator==(const Stride& rhs) const;
  bool operator!=(const Stride& rhs) const { return !(*this == rhs); }

  std::string ToString() const;

  // Getters and Setters
  const StrideVector& StrideVec() const { return stride_vec_; }
  int64_t NumAxes() const { return stride_vec_.size(); }
  int64_t At(int64_t index) const { return stride_vec_.at(index); }
  void Set(int64_t index, int64_t val) { stride_vec_.at(index) = val; }

 private:
  StrideVector stride_vec_;
};

}  // namespace oneflow

namespace std {

template<>
struct hash<oneflow::Stride> {
  size_t operator()(const oneflow::Stride& stride) const {
    size_t ret = 0;
    FOR_RANGE(int, i, 0, stride.NumAxes()) { ret ^= std::hash<int64_t>()(stride.At(i)); }
    return ret;
  }
};

}  // namespace std

#endif  // ONEFLOW_CORE_FRAMEWORK_STRIDE_H_

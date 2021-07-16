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
#ifndef ONEFLOW_CORE_KERNEL_UTIL_CUDA_BLAS_INTERFACE_H_
#define ONEFLOW_CORE_KERNEL_UTIL_CUDA_BLAS_INTERFACE_H_

#include "oneflow/core/kernel/util/blas_interface.h"

namespace oneflow {

class Blob;

template<>
struct BlasIf<DeviceType::kGPU> {
  static void OFGemm(DeviceCtx* ctx, enum CBLAS_TRANSPOSE trans_a, enum CBLAS_TRANSPOSE trans_b,
                     const int m, const int n, const int k, const double alpha, const float* a,
                     const float* b, const double beta, float* c);
  static void OFGemm(DeviceCtx* ctx, enum CBLAS_TRANSPOSE trans_a, enum CBLAS_TRANSPOSE trans_b,
                     const int m, const int n, const int k, const double alpha, const double* a,
                     const double* b, const double beta, double* c);
  static void OFGemm(DeviceCtx* ctx, enum CBLAS_TRANSPOSE trans_a, enum CBLAS_TRANSPOSE trans_b,
                     const int m, const int n, const int k, const double alpha, const float16* a,
                     const float16* b, const double beta, float16* c);

  static void OFBatchedGemm(DeviceCtx* ctx, enum CBLAS_TRANSPOSE trans_a,
                            enum CBLAS_TRANSPOSE trans_b, const int batch_size, const int m,
                            const int n, const int k, const double alpha, const float* a,
                            const float* b, const double beta, float* c);
  static void OFBatchedGemm(DeviceCtx* ctx, enum CBLAS_TRANSPOSE trans_a,
                            enum CBLAS_TRANSPOSE trans_b, const int batch_size, const int m,
                            const int n, const int k, const double alpha, const double* a,
                            const double* b, const double beta, double* c);
  static void OFBatchedGemm(DeviceCtx* ctx, enum CBLAS_TRANSPOSE trans_a,
                            enum CBLAS_TRANSPOSE trans_b, const int batch_size, const int m,
                            const int n, const int k, const double alpha, const float16* a,
                            const float16* b, const double beta, float16* c);

  static void Axpy(DeviceCtx* ctx, const int n, const float alpha, const float* x, const int incx,
                   float* y, const int incy);
  static void Axpy(DeviceCtx* ctx, const int n, const double alpha, const double* x, const int incx,
                   double* y, const int incy);
  static void Axpy(DeviceCtx* ctx, const int n, const float16 alpha, const float16* x,
                   const int incx, float16* y, const int incy);

  static void OFcuBlasSdot(DeviceCtx* ctx, const int n, const float* x, int incx, const float* y,
                           int incy, float* out);
  static void OFcuBlasDdot(DeviceCtx* ctx, const int n, const double* x, int incx, const double* y,
                           int incy, double* out);
};

}  // namespace oneflow

#endif  // ONEFLOW_CORE_KERNEL_UTIL_CUDA_BLAS_INTERFACE_H_

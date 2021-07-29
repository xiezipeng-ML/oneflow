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
#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include "oneflow/api/python/of_api_registry.h"
#include "oneflow/core/framework/dtype.h"
namespace py = pybind11;

namespace oneflow {

ONEFLOW_API_PYBIND11_MODULE("", m) {
  py::class_<Symbol<DType>, std::shared_ptr<Symbol<DType>>>(m, "dtype")
      .def_property_readonly("is_signed", [](const Symbol<DType>& d) { return d->is_signed(); })
      .def_property_readonly("is_complex", [](const Symbol<DType>& d) { return d->is_complex(); })
      .def_property_readonly("is_floating_point",
                             [](const Symbol<DType>& d) { return d->is_floating_point(); })
      .def("__str__", [](const Symbol<DType>& d) { return d->name(); })
      .def("__repr__", [](const Symbol<DType>& d) { return d->name(); })
      .def(py::self == py::self)
      .def(py::hash(py::self))
      .def_property_readonly(
          "bytes", [](const Symbol<DType>& dtype) { return dtype->bytes().GetOrThrow(); });

  m.attr("char") = DType::Char();
  m.attr("float16") = DType::Float16();
  m.attr("float") = DType::Float();

  m.attr("float32") = DType::Float();
  m.attr("double") = DType::Double();
  m.attr("float64") = DType::Double();

  m.attr("int8") = DType::Int8();
  m.attr("int32") = DType::Int32();
  m.attr("int64") = DType::Int64();

  m.attr("uint8") = DType::UInt8();
  m.attr("record") = DType::OFRecord();
  m.attr("tensor_buffer") = DType::TensorBuffer();

  // m.attr("char") = SymbolOf(*DType::Char());
  // m.attr("float16") = SymbolOf(*DType::Float16());
  // m.attr("float") = SymbolOf(*DType::Float());

  // m.attr("float32") = SymbolOf(*DType::Float());
  // m.attr("double") = SymbolOf(*DType::Double());
  // m.attr("float64") = SymbolOf(*DType::Double());

  // m.attr("int8") = SymbolOf(*DType::Int8());
  // m.attr("int32") = SymbolOf(*DType::Int32());
  // m.attr("int64") = SymbolOf(*DType::Int64());

  // m.attr("uint8") = SymbolOf(*DType::UInt8());
  // m.attr("record") = SymbolOf(*DType::OFRecord());
  // m.attr("tensor_buffer") = SymbolOf(*DType::TensorBuffer());

}

}  // namespace oneflow

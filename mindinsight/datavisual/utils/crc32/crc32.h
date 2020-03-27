/**
 * Copyright 2019 Huawei Technologies Co., Ltd
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef DATAVISUAL_UTILS_CRC32_CRC32_H_
#define DATAVISUAL_UTILS_CRC32_CRC32_H_

#include <pybind11/pybind11.h>
#include <stddef.h>
#include <cstdint>
#include "crc32/base.h"

// Align n to (1 << m) byte boundary
#define MEM_ALIGN(n, m) ((n + ((1 << m) - 1)) & ~((1 << m) - 1))

// Masked for crc.
static constexpr uint32 kMaskDelta = 0xa282ead8ul;

// Provide the Crc32c function

// Calculate the crc32c value, use the 8 table method
uint32 MakeCrc32c(uint32 init_crc, const char* data, size_t size);

uint32 GetMaskCrc32cValue(const char* data, size_t n) {
  auto crc = MakeCrc32c(0, data, n);
  return crc;
}

uint32 GetValueFromStr(const char* crc_str) {
  uint32 crc = DecodeFixed32(crc_str);
  uint32 rot = crc - kMaskDelta;
  return ((rot >> 17) | (rot << 15));
}

PYBIND11_MODULE(crc32, m) {
  m.doc() = "crc util";
  m.def("MakeCrc32c", &MakeCrc32c, "A function calculating the crc32c value, use the 8 table method");
  m.def("GetMaskCrc32cValue", &GetMaskCrc32cValue, "A function return the crc32c value");
  m.def("GetValueFromStr", &GetValueFromStr, "A function return the crc32c value from string");
}

#endif  // DATAVISUAL_UTILS_CRC32_CRC32_H_

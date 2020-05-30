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

#include <cstddef>
#include <cstdint>
#include "pybind11/pybind11.h"
#include "securec/include/securec.h"

#define CRC_TABLE_SIZE 256
#define RIGHT_SHIFT 15
#define LEFT_SHIFT 17

// Align n to (1 << m) byte boundary
#define MEM_ALIGN(n, m) ((n + ((1 << m) - 1)) & ~((1 << m) - 1))

// implement common define function
// Get the 32 bits align value
inline uint32_t DecodeFixed32(const char* ptr) {
  uint32_t result = 0;
  if (EOK != memcpy_s(&result, sizeof(result), ptr, sizeof(result))) {
    // `0` indicates that something wrong happened
    return 0;
  }
  return result;
}

// Used to fetch a naturally-aligned 32-bit word in little endian byte-order
inline uint32_t LE_LOAD32(const uint8_t* p) { return DecodeFixed32(reinterpret_cast<const char*>(p)); }

// Masked for crc.
static constexpr uint32_t kMaskDelta = 0xA282EAD8U;

// Provide the Crc32c function

// Calculate the crc32c value, use the 8 table method
uint32_t MakeCrc32c(uint32_t init_crc, const char* data, size_t size);

// A function return the crc32c value
uint32_t GetMaskCrc32cValue(const char* data, size_t n) {
  if (data == nullptr) {
    // Return early to prevent MakeCrc32c resulting in segmentfault
    return 0;
  }
  uint32_t crc = MakeCrc32c(0, data, n);
  return ((crc >> RIGHT_SHIFT) | (crc << LEFT_SHIFT)) + kMaskDelta;
}

// A function check the crc32c value against data
bool CheckValueAgainstData(const char* crc_str, const char* data, size_t size) {
  uint32_t crc_new = GetMaskCrc32cValue(data, size);
  uint32_t crc_old = DecodeFixed32(crc_str);
  return crc_new == crc_old;
}

PYBIND11_MODULE(crc32, m) {
  m.doc() = "crc util";
  m.def("GetMaskCrc32cValue", &GetMaskCrc32cValue, "A function return the crc32c value");
  m.def("CheckValueAgainstData", &CheckValueAgainstData, "A function check the crc32c value against data");
}

#endif  // DATAVISUAL_UTILS_CRC32_CRC32_H_

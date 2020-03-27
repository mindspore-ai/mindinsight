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

#ifndef DATAVISUAL_UTILS_CRC32_BASE_H_
#define DATAVISUAL_UTILS_CRC32_BASE_H_

#include <memory>
#include <string>
#include "securec/include/securec.h"

using string = std::string;

using int8 = int8_t;
using int16 = int16_t;
using int32 = int32_t;
using int64 = int64_t;

using uint8 = uint8_t;
using uint16 = uint16_t;
using uint32 = uint32_t;
using uint64 = uint64_t;

// check the null point, Only log it in if(): The value is null
#define EXCEPT_CHECK_NULL(value) \
  do {                           \
    if (value == nullptr) {      \
      break;                     \
    }                            \
  } while (0)

// implement common define function
// Get the 32 bits align value
inline uint32 DecodeFixed32(const char* ptr) {
  uint32 result = 0;
  if (EOK != memcpy_s(&result, sizeof(result), ptr, sizeof(result))) {
    return result;
  }
  return result;
}

// Used to fetch a naturally-aligned 32-bit word in little endian byte-order
inline uint32 LE_LOAD32(const uint8_t* p) { return DecodeFixed32(reinterpret_cast<const char*>(p)); }

#endif  // DATAVISUAL_UTILS_CRC32_BASE_H_

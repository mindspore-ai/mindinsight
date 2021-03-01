cmake_minimum_required(VERSION 3.14)

project(MindInsight)

find_package(Git QUIET)

if(GIT_FOUND AND EXISTS "${PROJECT_SOURCE_DIR}/.git")
    option(GIT_SUBMODULE "Check submodules during build" ON)
    if(GIT_SUBMODULE)
        message(STATUS "Updating submodules")
        execute_process(COMMAND ${GIT_EXECUTABLE} submodule update --init --recursive
                        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                        RESULT_VARIABLE GIT_SUBMOD_RESULT)
        if(NOT GIT_SUBMOD_RESULT EQUAL "0")
            message(FATAL_ERROR "git submodule update failed with ${GIT_SUBMOD_RESULT}, please checkout submodules.")
        endif()
    endif()
elseif(NOT EXISTS "${PROJECT_SOURCE_DIR}/third_party/securec/src")
    message(FATAL_ERROR "git command not found or not in a git repository, third_party/securec/src not exists.")
else()
    message(WARNING "git command not found or not in a git repository, submodules not updated.")
endif()

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE "Release")
endif()

set(CMAKE_C_FLAGS_DEBUG "$ENV{CFLAGS} -fPIC -O0 -Wall -fvisibility=hidden \
    -Wno-deprecated-declarations -g2 -ggdb -fno-inline-functions -fno-omit-frame-pointer \
    -D_LIBCPP_INLINE_VISIBILITY='' -D'_LIBCPP_EXTERN_TEMPLATE(...)='")
set(CMAKE_C_FLAGS_RELEASE "$ENV{CFLAGS} -fPIC -O3 -Wall -fvisibility=hidden -Wno-deprecated-declarations")
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

#add flags
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Werror")

include_directories(./third_party/securec/include)
aux_source_directory(./third_party/securec/src SECUREC_SRCS)
add_library(securec ${SECUREC_SRCS})

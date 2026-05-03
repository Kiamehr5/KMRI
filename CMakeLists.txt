cmake_minimum_required(VERSION 3.20)
project(kmri_core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Make pybind11 use modern FindPython3
set(PYBIND11_FINDPYTHON ON)

# Dependencies from vcpkg
find_package(pybind11 CONFIG REQUIRED)
find_package(zstd CONFIG REQUIRED)
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# Build Python extension
pybind11_add_module(kmri_core kmri_core.cpp)

target_link_libraries(kmri_core PRIVATE
    pybind11::module
    zstd::libzstd        # <-- this matches your zstdTargets.cmake
)

if (MSVC)
    target_compile_options(kmri_core PRIVATE /W0)
endif()

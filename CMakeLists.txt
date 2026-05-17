cmake_minimum_required(VERSION 3.16)
project(kmri_core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

execute_process(
    COMMAND ${Python3_EXECUTABLE} -m pybind11 --cmakedir
    OUTPUT_VARIABLE pybind11_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

list(APPEND CMAKE_PREFIX_PATH "${pybind11_DIR}")
find_package(pybind11 REQUIRED)

find_package(zstd CONFIG REQUIRED)

pybind11_add_module(kmri_core kmri_core.cpp)

target_link_libraries(kmri_core PRIVATE zstd::libzstd)

target_compile_options(kmri_core PRIVATE /O2)
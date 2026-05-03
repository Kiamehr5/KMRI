#include <vector>
#include <cstdint>
#include <stdexcept>
#include <zstd.h>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

// Compress a NumPy array into zstd bytes
py::bytes compress_chunk(py::array input, int level) {
    if (!(input.flags() & py::array::c_style)) {
        throw std::runtime_error("Input must be C-contiguous");
    }

    size_t input_size = input.nbytes();
    const void* input_ptr = input.data();

    size_t bound = ZSTD_compressBound(input_size);
    std::vector<uint8_t> out(bound);

    size_t csize = ZSTD_compress(out.data(), bound, input_ptr, input_size, level);
    if (ZSTD_isError(csize)) {
        throw std::runtime_error(ZSTD_getErrorName(csize));
    }

    return py::bytes(reinterpret_cast<const char*>(out.data()), csize);
}

// Decompress zstd bytes into a NumPy array
py::array decompress_chunk(py::bytes input_bytes,
                           py::tuple shape,
                           py::dtype dtype) {
    std::string buf = input_bytes;
    const void* input_ptr = buf.data();
    size_t input_size = buf.size();

    Py_ssize_t ndim = shape.size();
    std::vector<Py_ssize_t> dims(ndim);

    size_t itemsize = dtype.itemsize();
    size_t output_size = itemsize;

    for (Py_ssize_t i = 0; i < ndim; ++i) {
        dims[i] = shape[i].cast<Py_ssize_t>();
        output_size *= static_cast<size_t>(dims[i]);
    }

    std::vector<uint8_t> out(output_size);
    size_t rsize = ZSTD_decompress(out.data(), output_size, input_ptr, input_size);
    if (ZSTD_isError(rsize)) {
        throw std::runtime_error(ZSTD_getErrorName(rsize));
    }

    py::array arr(dtype, dims);
    std::memcpy(arr.mutable_data(), out.data(), output_size);
    return arr;

}

PYBIND11_MODULE(kmri_core, m) {
    m.doc() = "KMRI C++ core with zstd compression";

    m.def("compress_chunk", &compress_chunk,
          py::arg("input"), py::arg("level") = 3);

    m.def("decompress_chunk", &decompress_chunk,
          py::arg("input_bytes"), py::arg("shape"), py::arg("dtype"));
}

//example.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <omp.h>
#include <iostream>
#include <vector>
#include <utility>
#include <ctime>

//#include <windows.h>
//#undef max
//#undef min

#include "utils/scene_tree.h"

namespace py = pybind11;

PYBIND11_MODULE(SceneTreeCPP, m) {
    m.doc() = "Scene Tree"; // optional module docstring
    m.def("HierarchyMerge", &HierarchyMerge, py::call_guard<py::gil_scoped_release>(), "A function to get scene tree");
}
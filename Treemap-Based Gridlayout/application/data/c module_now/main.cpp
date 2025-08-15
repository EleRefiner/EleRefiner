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

#include "utils/treemap.h"

PYBIND11_MODULE(GridBasedTreeMap, m) {
    m.doc() = "Grid-Based TreeMap"; // optional module docstring
    m.def("SearchForTree", &SearchForTree, "A function to get treemap");
    m.def("SearchForTree2", &SearchForTree2, "A function to get treemap");
}
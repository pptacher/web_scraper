cmake_minimum_required(VERSION 2.8 FATAL_ERROR)

find_package(CURL REQUIRED)
include_directories( /usr/local/include /usr/local/include/re2)
link_directories(/usr/local/lib)
list(APPEND CMAKE_CXX_FLAGS "-std=c++17")

add_executable(booking.bin booking.cc)
target_link_libraries(booking.bin curl re2)

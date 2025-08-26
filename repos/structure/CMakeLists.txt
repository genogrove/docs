cmake_minimum_required(VERSION 3.10)
project(genogrove_structure)

set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 20)

include(FetchContent)

# check if c++ standard is set
if(NOT DEFINED CMAKE_CXX_STANDARD)
    message(STATUS "C++ standard not set, defaulting to C++20")
    set(CMAKE_CXX_STANDARD 20)
endif()

# load config
if(NOT TARGET genogrove_config)
    FetchContent_Declare(
            genogrove_config
            GIT_REPOSITORY https://github.com/genogrove/config.git
            GIT_TAG main
    )
    FetchContent_MakeAvailable(genogrove_config)
endif()

# load utiltiy
if(NOT TARGET genogrove_utility)
    FetchContent_Declare(
            genogrove_utility
            GIT_REPOSITORY https://github.com/genogrove/utility.git
            GIT_TAG main
    )
    FetchContent_MakeAvailable(genogrove_utility)
endif()

# load data type
if(NOT TARGET genogrove_data_type)
    FetchContent_Declare(
            genogrove_data_type
            GIT_REPOSITORY https://github.com/genogrove/data_type.git
            GIT_TAG main
    )
    FetchContent_MakeAvailable(genogrove_data_type)
endif()

FILE(GLOB SOURCES "src/*.cpp")
add_library(genogrove_structure ${SOURCES}
        include/genogrove/structure/grove/key.hpp)
target_include_directories(genogrove_structure
        PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
)

target_link_libraries(genogrove_structure
        PUBLIC
        genogrove_config
        genogrove_utility
        genogrove_data_type)

if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(test)
endif()








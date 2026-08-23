cmake_minimum_required(VERSION 3.16...3.30)
project(GAGGSurfaceStudy VERSION 0.1.0 LANGUAGES CXX)

find_package(Geant4 11.2 REQUIRED)
include(${Geant4_USE_FILE})

add_executable(gagg_surface_study
  app/main.cc
  src/DetectorConstruction.cc
  src/PhysicsList.cc
  src/PrimaryGeneratorAction.cc
)
target_include_directories(gagg_surface_study PRIVATE ${PROJECT_SOURCE_DIR}/include)
target_compile_features(gagg_surface_study PRIVATE cxx_std_17)
target_compile_options(gagg_surface_study PRIVATE -Wall -Wextra -Wpedantic)
target_link_libraries(gagg_surface_study PRIVATE ${Geant4_LIBRARIES})

file(COPY macros DESTINATION ${PROJECT_BINARY_DIR})

include(CTest)
if(BUILD_TESTING)
  add_test(
    NAME smoke
    COMMAND $<TARGET_FILE:gagg_surface_study>
            ${PROJECT_BINARY_DIR}/macros/validation/smoke.mac
  )
  set_tests_properties(smoke PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[smoke\\] run completed"
    FAIL_REGULAR_EXPRESSION "unclassified=[1-9][0-9]*|G4Exception|Fatal Exception"
  )
endif()

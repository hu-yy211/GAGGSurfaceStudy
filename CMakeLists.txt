cmake_minimum_required(VERSION 3.16...3.30)
project(GAGGSurfaceStudy VERSION 0.1.0 LANGUAGES CXX)

find_package(Geant4 11.2 REQUIRED ui_all vis_all)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
include(${Geant4_USE_FILE})

add_executable(gagg_surface_study
  app/main.cc
  src/DetectorConstruction.cc
  src/EventAction.cc
  src/MaterialValidation.cc
  src/PhysicsList.cc
  src/PrimaryGeneratorAction.cc
  src/RunAction.cc
  src/SteppingAction.cc
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

  add_test(
    NAME a0_csv_export
    COMMAND $<TARGET_FILE:gagg_surface_study>
            ${PROJECT_BINARY_DIR}/macros/validation/a0_csv_test.mac
  )
  set_tests_properties(a0_csv_export PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[output\\] csv=.*a0_test_events.csv rows=25"
    FAIL_REGULAR_EXPRESSION "unclassified=[1-9][0-9]*|G4Exception|Fatal Exception"
  )

  add_test(
    NAME a0_csv_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_a0_csv.py
            --input ${PROJECT_BINARY_DIR}/a0_test_events.csv
            --expect-events 25
  )
  set_tests_properties(a0_csv_validate PROPERTIES
    DEPENDS a0_csv_export
    PASS_REGULAR_EXPRESSION "\\[csv-check\\].*status=PASS"
  )

  add_test(
    NAME a0_plot
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/plot_a0.py
            --input ${PROJECT_BINARY_DIR}/a0_test_events.csv
            --output-dir ${PROJECT_BINARY_DIR}/a0_plots
  )
  set_tests_properties(a0_plot PROPERTIES
    DEPENDS a0_csv_validate
    ENVIRONMENT "MPLCONFIGDIR=${PROJECT_BINARY_DIR}/.mplconfig"
    PASS_REGULAR_EXPRESSION "\\[plot\\] status=PASS"
  )

  add_test(
    NAME a1_material_units
    COMMAND $<TARGET_FILE:gagg_surface_study> --validate-materials
  )
  set_tests_properties(a1_material_units PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[a1\\] material_units status=PASS"
    FAIL_REGULAR_EXPRESSION "status=FAIL|G4Exception|Fatal Exception"
  )
endif()

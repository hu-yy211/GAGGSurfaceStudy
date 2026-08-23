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
  src/StackingAction.cc
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

  add_test(
    NAME a2_paper_geometry
    COMMAND $<TARGET_FILE:gagg_surface_study>
            ${PROJECT_BINARY_DIR}/macros/validation/a2_geometry.mac
  )
  set_tests_properties(a2_paper_geometry PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[a2\\] geometry status=PASS"
    FAIL_REGULAR_EXPRESSION "status=FAIL|Overlap with volume|G4Exception|Fatal Exception"
  )

  add_test(
    NAME a3_transport_export
    COMMAND $<TARGET_FILE:gagg_surface_study>
            ${PROJECT_BINARY_DIR}/macros/validation/a3_transport.mac
  )
  set_tests_properties(a3_transport_export PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[output\\] csv=results/a3/z_p10.csv rows=100"
    FAIL_REGULAR_EXPRESSION "unclassified=[1-9][0-9]*|status=FAIL|G4Exception|Fatal Exception"
  )

  add_test(
    NAME a3_no_absorption_export
    COMMAND $<TARGET_FILE:gagg_surface_study>
            ${PROJECT_BINARY_DIR}/macros/validation/a3_no_absorption.mac
  )
  set_tests_properties(a3_no_absorption_export PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[output\\] csv=results/a3/center_no_absorption.csv rows=100"
    FAIL_REGULAR_EXPRESSION "unclassified=[1-9][0-9]*|status=FAIL|G4Exception|Fatal Exception"
  )

  add_test(
    NAME a3_transport_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_a3.py
            --center-a ${PROJECT_BINARY_DIR}/results/a3/center_a.csv
            --center-b ${PROJECT_BINARY_DIR}/results/a3/center_b.csv
            --no-absorption ${PROJECT_BINARY_DIR}/results/a3/center_no_absorption.csv
            --z-m10 ${PROJECT_BINARY_DIR}/results/a3/z_m10.csv
            --z-m5 ${PROJECT_BINARY_DIR}/results/a3/z_m5.csv
            --z-p5 ${PROJECT_BINARY_DIR}/results/a3/z_p5.csv
            --z-p10 ${PROJECT_BINARY_DIR}/results/a3/z_p10.csv
  )
  set_tests_properties(a3_transport_validate PROPERTIES
    DEPENDS "a3_transport_export;a3_no_absorption_export"
    PASS_REGULAR_EXPRESSION "\\[a3\\] transport status=PASS"
  )

  add_test(
    NAME a3_plot
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/plot_a3.py
            --input-dir ${PROJECT_BINARY_DIR}/results/a3
            --output-dir ${PROJECT_BINARY_DIR}/a3_plots
  )
  set_tests_properties(a3_plot PROPERTIES
    DEPENDS a3_transport_validate
    ENVIRONMENT "MPLCONFIGDIR=${PROJECT_BINARY_DIR}/.mplconfig"
    PASS_REGULAR_EXPRESSION "\\[a3-plot\\] status=PASS"
  )

  add_test(
    NAME a4_surface_export
    COMMAND $<TARGET_FILE:gagg_surface_study>
            ${PROJECT_BINARY_DIR}/macros/stage_a/a4_compare.mac
  )
  set_tests_properties(a4_surface_export PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[output\\] csv=results/a4/polishedvm2000air_repeat.csv rows=50"
    FAIL_REGULAR_EXPRESSION "unclassified=[1-9][0-9]*|status=FAIL|G4Exception|Fatal Exception"
    TIMEOUT 300
  )

  add_test(
    NAME a4_surface_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_a4.py
            --input-dir ${PROJECT_BINARY_DIR}/results/a4
  )
  set_tests_properties(a4_surface_validate PROPERTIES
    DEPENDS a4_surface_export
    PASS_REGULAR_EXPRESSION "\\[a4-check\\] lut_switching status=PASS"
  )

  add_test(
    NAME a4_plot
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/plot_a4.py
            --input-dir ${PROJECT_BINARY_DIR}/results/a4
            --output-dir ${PROJECT_BINARY_DIR}/a4_plots
  )
  set_tests_properties(a4_plot PROPERTIES
    DEPENDS a4_surface_validate
    ENVIRONMENT "MPLCONFIGDIR=${PROJECT_BINARY_DIR}/.mplconfig"
    PASS_REGULAR_EXPRESSION "\\[a4-plot\\] status=PASS"
  )

  add_test(
    NAME a5_linearity_export
    COMMAND $<TARGET_FILE:gagg_surface_study>
            ${PROJECT_BINARY_DIR}/macros/validation/a5_linearity.mac
  )
  set_tests_properties(a5_linearity_export PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[output\\] csv=results/a5/energy_40kev.csv rows=20"
    FAIL_REGULAR_EXPRESSION "unclassified=[1-9][0-9]*|status=FAIL|G4Exception|Fatal Exception"
    TIMEOUT 300
  )

  add_test(
    NAME a5_slow_time_export
    COMMAND $<TARGET_FILE:gagg_surface_study>
            ${PROJECT_BINARY_DIR}/macros/validation/a5_slow_time.mac
  )
  set_tests_properties(a5_slow_time_export PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[output\\] csv=results/a5/energy_20kev_slow.csv rows=20"
    FAIL_REGULAR_EXPRESSION "unclassified=[1-9][0-9]*|status=FAIL|G4Exception|Fatal Exception"
    TIMEOUT 300
  )

  add_test(
    NAME a5_scintillation_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_a5.py
            --input-dir ${PROJECT_BINARY_DIR}/results/a5
  )
  set_tests_properties(a5_scintillation_validate PROPERTIES
    DEPENDS "a5_linearity_export;a5_slow_time_export"
    PASS_REGULAR_EXPRESSION "\\[a5-check\\] scintillation status=PASS"
  )

  add_test(
    NAME a5_plot
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/plot_a5.py
            --input-dir ${PROJECT_BINARY_DIR}/results/a5
            --output-dir ${PROJECT_BINARY_DIR}/a5_plots
  )
  set_tests_properties(a5_plot PROPERTIES
    DEPENDS a5_scintillation_validate
    ENVIRONMENT "MPLCONFIGDIR=${PROJECT_BINARY_DIR}/.mplconfig"
    PASS_REGULAR_EXPRESSION "\\[a5-plot\\] status=PASS"
  )
endif()

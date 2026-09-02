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

  add_test(
    NAME a6_gamma_export
    COMMAND $<TARGET_FILE:gagg_surface_study>
            ${PROJECT_BINARY_DIR}/macros/validation/a6_gamma.mac
  )
  set_tests_properties(a6_gamma_export PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[output\\] csv=results/a6/gamma_662kev.csv rows=100"
    FAIL_REGULAR_EXPRESSION "unclassified=[1-9][0-9]*|status=FAIL|G4Exception|Fatal Exception"
    TIMEOUT 300
  )

  add_test(
    NAME a6_gamma_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_a6.py
            --input ${PROJECT_BINARY_DIR}/results/a6/gamma_662kev.csv
            --expect-events 100
  )
  set_tests_properties(a6_gamma_validate PROPERTIES
    DEPENDS a6_gamma_export
    PASS_REGULAR_EXPRESSION "\\[a6-check\\] gamma status=PASS"
  )

  add_test(
    NAME a6_plot
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/plot_a6.py
            --input ${PROJECT_BINARY_DIR}/results/a6/gamma_662kev.csv
            --output-dir ${PROJECT_BINARY_DIR}/a6_plots
  )
  set_tests_properties(a6_plot PROPERTIES
    DEPENDS a6_gamma_validate
    ENVIRONMENT "MPLCONFIGDIR=${PROJECT_BINARY_DIR}/.mplconfig"
    PASS_REGULAR_EXPRESSION "\\[a6-plot\\] status=PASS"
  )

  add_test(
    NAME b0_experiment_geometry
    COMMAND $<TARGET_FILE:gagg_surface_study>
            ${PROJECT_BINARY_DIR}/macros/validation/b0_geometry.mac
  )
  set_tests_properties(b0_experiment_geometry PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[b0\\] geometry status=PASS"
    FAIL_REGULAR_EXPRESSION "status=FAIL|Overlap with volume|G4Exception|Fatal Exception"
  )

  add_test(
    NAME b0_transport_export
    COMMAND $<TARGET_FILE:gagg_surface_study>
            ${PROJECT_BINARY_DIR}/macros/validation/b0_transport.mac
  )
  set_tests_properties(b0_transport_export PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[output\\] csv=results/b0/b0_transport.csv rows=50"
    FAIL_REGULAR_EXPRESSION "unclassified=[1-9][0-9]*|status=FAIL|G4Exception|Fatal Exception"
    TIMEOUT 300
  )

  add_test(
    NAME b0_transport_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_b0.py
            --input ${PROJECT_BINARY_DIR}/results/b0/b0_transport.csv
            --expect-events 50
            --photons-per-event 100
  )
  set_tests_properties(b0_transport_validate PROPERTIES
    DEPENDS b0_transport_export
    PASS_REGULAR_EXPRESSION "\\[b0-check\\].*status=PASS"
  )

  add_test(
    NAME b7_1_face_source_export
    COMMAND $<TARGET_FILE:gagg_surface_study>
            ${PROJECT_BINARY_DIR}/macros/validation/b7_face_source.mac
  )
  set_tests_properties(b7_1_face_source_export PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[output\\] csv=results/b7_1_face_source/positions.csv rows=5000"
    FAIL_REGULAR_EXPRESSION "unclassified=[1-9][0-9]*|status=FAIL|G4Exception|Fatal Exception"
    TIMEOUT 300
  )

  add_test(
    NAME b7_1_face_source_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_b7_face_source.py
            --input ${PROJECT_BINARY_DIR}/results/b7_1_face_source/positions.csv
            --output-dir ${PROJECT_BINARY_DIR}/results/b7_1_face_source/figures
            --expect-events 5000
            --face-size-mm 2.5
  )
  set_tests_properties(b7_1_face_source_validate PROPERTIES
    DEPENDS b7_1_face_source_export
    ENVIRONMENT "MPLCONFIGDIR=${PROJECT_BINARY_DIR}/.mplconfig"
    PASS_REGULAR_EXPRESSION "\\[b7.1\\] face_source_sampling status=PASS"
  )

  add_test(
    NAME b7_2_annihilation_pair_export
    COMMAND $<TARGET_FILE:gagg_surface_study>
            ${PROJECT_BINARY_DIR}/macros/validation/b7_annihilation_pair_source.mac
  )
  set_tests_properties(b7_2_annihilation_pair_export PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[b7.2-source\\] audit_csv=.*source_audit.csv rows=10000"
    FAIL_REGULAR_EXPRESSION "unclassified=[1-9][0-9]*|status=FAIL|G4Exception|Fatal Exception"
    TIMEOUT 300
  )

  add_test(
    NAME b7_2_annihilation_pair_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_b7_annihilation_pair.py
            --input ${PROJECT_BINARY_DIR}/results/b7_2_annihilation_pair/source_audit.csv
            --output-dir ${PROJECT_BINARY_DIR}/results/b7_2_annihilation_pair/figures
            --expect-events 10000
            --face-size-mm 2.5
  )
  set_tests_properties(b7_2_annihilation_pair_validate PROPERTIES
    DEPENDS b7_2_annihilation_pair_export
    ENVIRONMENT "MPLCONFIGDIR=${PROJECT_BINARY_DIR}/.mplconfig"
    PASS_REGULAR_EXPRESSION "\\[b7.2\\] annihilation_pair_source status=PASS"
  )

  add_test(
    NAME b7_3_full_energy_export
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/run_b7_3.py
            --executable $<TARGET_FILE:gagg_surface_study>
            --config ${PROJECT_SOURCE_DIR}/config/b7_3_full_energy_response.json
            --output-dir ${PROJECT_BINARY_DIR}/results/b7_3_full_energy
  )
  set_tests_properties(b7_3_full_energy_export PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[b7.3-runner\\].*events=100000.*status=PASS"
    FAIL_REGULAR_EXPRESSION "unclassified=[1-9][0-9]*|status=FAIL|G4Exception|Fatal Exception"
    TIMEOUT 1800
  )

  add_test(
    NAME b7_3_full_energy_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_b7_3.py
            --input ${PROJECT_BINARY_DIR}/results/b7_3_full_energy/annihilation_pair_all_polished.csv
            --config ${PROJECT_SOURCE_DIR}/config/b7_3_full_energy_response.json
  )
  set_tests_properties(b7_3_full_energy_validate PROPERTIES
    DEPENDS b7_3_full_energy_export
    PASS_REGULAR_EXPRESSION "\\[b7.3-check\\] event_level_511_gate=true.*status=PASS"
  )

  add_test(
    NAME b7_3_plot
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/plot_b7_3.py
            --input ${PROJECT_BINARY_DIR}/results/b7_3_full_energy/annihilation_pair_all_polished.csv
            --output-dir ${PROJECT_BINARY_DIR}/results/b7_3_full_energy/figures
            --config ${PROJECT_SOURCE_DIR}/config/b7_3_full_energy_response.json
  )
  set_tests_properties(b7_3_plot PROPERTIES
    DEPENDS b7_3_full_energy_validate
    ENVIRONMENT "MPLCONFIGDIR=${PROJECT_BINARY_DIR}/.mplconfig"
    PASS_REGULAR_EXPRESSION "\\[b7.3-plot\\].*status=PASS"
  )

  add_test(
    NAME b1_surface_export
    COMMAND $<TARGET_FILE:gagg_surface_study>
            ${PROJECT_BINARY_DIR}/macros/stage_b/b1_compare.mac
  )
  set_tests_properties(b1_surface_export PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[output\\] csv=results/b1/all_polished_repeat.csv rows=50"
    FAIL_REGULAR_EXPRESSION "unclassified=[1-9][0-9]*|status=FAIL|G4Exception|Fatal Exception"
    TIMEOUT 300
  )

  add_test(
    NAME b1_surface_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_b1.py
            --input-dir ${PROJECT_BINARY_DIR}/results/b1
            --expect-events 50
            --photons-per-event 100
            --sigma-alpha 0.20
  )
  set_tests_properties(b1_surface_validate PROPERTIES
    DEPENDS b1_surface_export
    PASS_REGULAR_EXPRESSION "\\[b1-check\\].*six_state_switching=true.*status=PASS"
  )

  add_test(
    NAME b1_plot
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/plot_b1.py
            --input-dir ${PROJECT_BINARY_DIR}/results/b1
            --output-dir ${PROJECT_BINARY_DIR}/b1_plots
            --expect-events 50
            --photons-per-event 100
            --sigma-alpha 0.20
  )
  set_tests_properties(b1_plot PROPERTIES
    DEPENDS b1_surface_validate
    ENVIRONMENT "MPLCONFIGDIR=${PROJECT_BINARY_DIR}/.mplconfig"
    PASS_REGULAR_EXPRESSION "\\[b1-plot\\].*status=PASS"
  )

  add_test(
    NAME b2_scan_export
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/run_b2_scan.py
            --executable $<TARGET_FILE:gagg_surface_study>
            --config ${PROJECT_SOURCE_DIR}/config/b2_scan.json
            --output-dir ${PROJECT_BINARY_DIR}/results/b2
  )
  set_tests_properties(b2_scan_export PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[b2-runner\\].*points=90.*status=PASS"
    FAIL_REGULAR_EXPRESSION "status=FAIL|G4Exception|Fatal Exception"
    TIMEOUT 600
  )

  add_test(
    NAME b2_scan_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_b2.py
            --input-dir ${PROJECT_BINARY_DIR}/results/b2
            --config ${PROJECT_SOURCE_DIR}/config/b2_scan.json
  )
  set_tests_properties(b2_scan_validate PROPERTIES
    DEPENDS b2_scan_export
    PASS_REGULAR_EXPRESSION "\\[b2-check\\].*points=90.*status=PASS"
  )

  add_test(
    NAME b2_plot
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/plot_b2.py
            --input-dir ${PROJECT_BINARY_DIR}/results/b2
            --output-dir ${PROJECT_BINARY_DIR}/b2_plots
            --config ${PROJECT_SOURCE_DIR}/config/b2_scan.json
  )
  set_tests_properties(b2_plot PROPERTIES
    DEPENDS b2_scan_validate
    ENVIRONMENT "MPLCONFIGDIR=${PROJECT_BINARY_DIR}/.mplconfig"
    PASS_REGULAR_EXPRESSION "\\[b2-plot\\].*status=PASS"
  )

  add_test(
    NAME b3_gamma_export
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/run_b3.py
            --executable $<TARGET_FILE:gagg_surface_study>
            --config ${PROJECT_SOURCE_DIR}/config/b3_gamma.json
            --output-dir ${PROJECT_BINARY_DIR}/results/b3
  )
  set_tests_properties(b3_gamma_export PROPERTIES
    PASS_REGULAR_EXPRESSION "\\[b3-runner\\].*gamma_keV=511.*status=PASS"
    FAIL_REGULAR_EXPRESSION "status=FAIL|G4Exception|Fatal Exception"
    TIMEOUT 600
  )

  add_test(
    NAME b3_gamma_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_b3.py
            --input ${PROJECT_BINARY_DIR}/results/b3/gamma_511kev_all_polished.csv
            --config ${PROJECT_SOURCE_DIR}/config/b3_gamma.json
  )
  set_tests_properties(b3_gamma_validate PROPERTIES
    DEPENDS b3_gamma_export
    PASS_REGULAR_EXPRESSION "\\[b3-check\\] gamma_511 status=PASS"
  )

  add_test(
    NAME b3_plot
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/plot_b3.py
            --input ${PROJECT_BINARY_DIR}/results/b3/gamma_511kev_all_polished.csv
            --output-dir ${PROJECT_BINARY_DIR}/b3_plots
            --config ${PROJECT_SOURCE_DIR}/config/b3_gamma.json
  )
  set_tests_properties(b3_plot PROPERTIES
    DEPENDS b3_gamma_validate
    ENVIRONMENT "MPLCONFIGDIR=${PROJECT_BINARY_DIR}/.mplconfig"
    PASS_REGULAR_EXPRESSION "\\[b3-plot\\].*status=PASS"
  )

  add_test(
    NAME b4_comparison_export
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/run_b4.py
            --executable $<TARGET_FILE:gagg_surface_study>
            --config ${PROJECT_SOURCE_DIR}/config/b4_comparison.json
            --output-dir ${PROJECT_BINARY_DIR}/results/b4
  )
  set_tests_properties(b4_comparison_export PROPERTIES
    DEPENDS b3_gamma_export
    PASS_REGULAR_EXPRESSION "\\[b4-runner\\].*states=6.*shared_sigma=true.*status=PASS"
    FAIL_REGULAR_EXPRESSION "status=FAIL|G4Exception|Fatal Exception"
    TIMEOUT 1800
  )

  add_test(
    NAME b4_comparison_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_b4.py
            --input-dir ${PROJECT_BINARY_DIR}/results/b4
            --b3-reference ${PROJECT_BINARY_DIR}/results/b3/gamma_511kev_all_polished.csv
            --config ${PROJECT_SOURCE_DIR}/config/b4_comparison.json
  )
  set_tests_properties(b4_comparison_validate PROPERTIES
    DEPENDS b4_comparison_export
    PASS_REGULAR_EXPRESSION "\\[b4-check\\] six_state_comparison status=PASS"
  )

  add_test(
    NAME b4_plot
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/plot_b4.py
            --input-dir ${PROJECT_BINARY_DIR}/results/b4
            --output-dir ${PROJECT_BINARY_DIR}/b4_plots
            --config ${PROJECT_SOURCE_DIR}/config/b4_comparison.json
  )
  set_tests_properties(b4_plot PROPERTIES
    DEPENDS b4_comparison_validate
    ENVIRONMENT "MPLCONFIGDIR=${PROJECT_BINARY_DIR}/.mplconfig"
    PASS_REGULAR_EXPRESSION "\\[b4-plot\\].*status=PASS"
  )

  add_test(
    NAME b5_robustness_export
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/run_b5.py
            --executable $<TARGET_FILE:gagg_surface_study>
            --config ${PROJECT_SOURCE_DIR}/config/b5_robustness.json
            --output-dir ${PROJECT_BINARY_DIR}/results/b5
  )
  set_tests_properties(b5_robustness_export PROPERTIES
    DEPENDS b4_comparison_export
    PASS_REGULAR_EXPRESSION "\\[b5-runner\\].*points=12.*shared_sigma=true.*status=PASS"
    FAIL_REGULAR_EXPRESSION "status=FAIL|G4Exception|Fatal Exception"
    TIMEOUT 1800
  )

  add_test(
    NAME b5_robustness_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_b5.py
            --input-dir ${PROJECT_BINARY_DIR}/results/b5
            --b4-input-dir ${PROJECT_BINARY_DIR}/results/b4
            --config ${PROJECT_SOURCE_DIR}/config/b5_robustness.json
  )
  set_tests_properties(b5_robustness_validate PROPERTIES
    DEPENDS b5_robustness_export
    PASS_REGULAR_EXPRESSION "\\[b5-check\\] robustness status=PASS"
  )

  add_test(
    NAME b5_plot
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/plot_b5.py
            --input-dir ${PROJECT_BINARY_DIR}/results/b5
            --b4-input-dir ${PROJECT_BINARY_DIR}/results/b4
            --output-dir ${PROJECT_BINARY_DIR}/b5_plots
            --config ${PROJECT_SOURCE_DIR}/config/b5_robustness.json
  )
  set_tests_properties(b5_plot PROPERTIES
    DEPENDS b5_robustness_validate
    ENVIRONMENT "MPLCONFIGDIR=${PROJECT_BINARY_DIR}/.mplconfig"
    PASS_REGULAR_EXPRESSION "\\[b5-plot\\].*status=PASS"
  )

  add_test(
    NAME b6_loss_diagnostics_validate
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/validate_b6.py
            --input-dir ${PROJECT_BINARY_DIR}/results/b5
            --b4-input-dir ${PROJECT_BINARY_DIR}/results/b4
            --config ${PROJECT_SOURCE_DIR}/config/b6_diagnostics.json
  )
  set_tests_properties(b6_loss_diagnostics_validate PROPERTIES
    DEPENDS b5_robustness_validate
    PASS_REGULAR_EXPRESSION "\\[b6-check\\] loss_diagnostics status=PASS"
  )

  add_test(
    NAME b6_plot
    COMMAND ${Python3_EXECUTABLE}
            ${PROJECT_SOURCE_DIR}/analysis/plot_b6.py
            --input-dir ${PROJECT_BINARY_DIR}/results/b5
            --b4-input-dir ${PROJECT_BINARY_DIR}/results/b4
            --output-dir ${PROJECT_BINARY_DIR}/b6_plots
            --config ${PROJECT_SOURCE_DIR}/config/b6_diagnostics.json
  )
  set_tests_properties(b6_plot PROPERTIES
    DEPENDS b6_loss_diagnostics_validate
    ENVIRONMENT "MPLCONFIGDIR=${PROJECT_BINARY_DIR}/.mplconfig"
    PASS_REGULAR_EXPRESSION "\\[b6-plot\\].*status=PASS"
  )
endif()

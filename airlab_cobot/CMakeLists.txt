cmake_minimum_required(VERSION 3.8)
project(airlab_cobot)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()


set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)


find_package(QT NAMES Qt6 Qt5 REQUIRED COMPONENTS Widgets Sql)
find_package(Qt${QT_VERSION_MAJOR} REQUIRED COMPONENTS Widgets Sql)

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(sensor_msgs REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)
include_directories(include)
set(PROJECT_SOURCES
        src/airlab_cobot_qt_control.cpp
        src/mainwindow.cpp
        include/mainwindow.h
        src/mainwindow.ui
)

add_executable(airlab_cobot_qt_control ${PROJECT_SOURCES})

target_link_libraries(airlab_cobot_qt_control

Qt${QT_VERSION_MAJOR}::Widgets
Qt${QT_VERSION_MAJOR}::Sql
)


target_include_directories(airlab_cobot_qt_control PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
target_compile_features(airlab_cobot_qt_control PUBLIC c_std_99 cxx_std_17)  # Require C99 and C++17

ament_target_dependencies(
  airlab_cobot_qt_control
  "rclcpp"
  "rclcpp_components"
  "sensor_msgs"
)

install(DIRECTORY launch
DESTINATION share/${PROJECT_NAME})

install(DIRECTORY config
DESTINATION share/${PROJECT_NAME})


install(TARGETS airlab_cobot_qt_control
  DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()

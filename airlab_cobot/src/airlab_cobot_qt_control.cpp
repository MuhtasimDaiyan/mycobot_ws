#include "mainwindow.h"

#include <QApplication>
#include <rclcpp/rclcpp.hpp>
#include <thread>

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    QApplication app(argc, argv);

    auto window = std::make_shared<MainWindow>();
    window->show();

    // Run ROS2 in a background thread
    rclcpp::executors::SingleThreadedExecutor executor;
    executor.add_node(window);

    std::thread ros_thread([&executor]() {
        executor.spin();
    });

    int ret = app.exec();

    // Clean shutdown
    executor.cancel();
    ros_thread.join();
    rclcpp::shutdown();

    return ret;
}

#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <algorithm>
#include <rclcpp/rclcpp.hpp>
#include "database.h"
#include <sensor_msgs/msg/joint_state.hpp>



#include <algorithm>   // std::clamp
#include <array>

static constexpr std::array<double, 6> JOINT_LOWER = {
    -2.9322,   // joint2_to_joint1
    -2.3562,   // joint3_to_joint2
    -2.6180,   // joint4_to_joint3
    -2.5307,   // joint5_to_joint4
    -2.8798,   // joint6_to_joint5
    -3.14159   // joint6output_to_joint6
};

static constexpr std::array<double, 6> JOINT_UPPER = {
     2.9322,
     2.3562,
     2.6180,
     2.5307,
     2.8798,
     3.14159
};

const float ARM_LENGTH = 0.28; // meters
const float VOXEL_SIZE = 0.04; // meters

struct Coord{
    float x, y, z;
    Coord(): x(0), y(0), z(0) {}

    void set_dx(int pos)
    {
        float dx = static_cast<float>(pos - last_x) * VOXEL_SIZE;
        x = std::clamp(x + dx, -ARM_LENGTH, ARM_LENGTH);
        last_x = pos;
    
    }
    void set_dy(int pos)
    {
        float dy = static_cast<float>(pos - last_y) * VOXEL_SIZE;
        y = std::clamp(y + dy, -ARM_LENGTH, ARM_LENGTH);
        last_y = pos;
    }
    void set_dz(int pos)
    {
        float dz = static_cast<float>(pos - last_y) * VOXEL_SIZE;
        z = std::clamp(z + dz, 0.0f, ARM_LENGTH);
        last_z = pos;
    }
private:
    int last_x = 0; 
    int last_y = 0; 
    int last_z = 0;


};



QT_BEGIN_NAMESPACE
namespace Ui {
class MainWindow;
}
QT_END_NAMESPACE

class MainWindow : public QMainWindow, public rclcpp::Node
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void on_targetButton_clicked();

    void on_dial_sliderMoved(int position);

    void on_inputText_returnPressed();

    void on_verticalSlider_sliderMoved(int position);

    void on_horizontalSlider_sliderMoved(int position);

    void on_verticalSlider_2_sliderMoved(int position);

    

private:
    Ui::MainWindow *ui;
    Coord endEffector;
    std::string db_path;
    DbmPtr db_;
    rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr joint_state_pub_;
    int dial_last_pos = 0;
protected:
    void updateMsg();
    std::array<double, 6> getJointValuesFromDB();
    void publishJointState(const std::array<double, 6>& joint_values);

};
#endif // MAINWINDOW_H

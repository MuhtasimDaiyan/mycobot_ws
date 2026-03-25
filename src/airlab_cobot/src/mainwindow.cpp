#include "mainwindow.h"
#include "./ui_mainwindow.h"
#include <cmath>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow),
    rclcpp::Node("airlab_cobot_qt_control")
{
    ui->setupUi(this);
    this->declare_parameter("db_path", "/home/redwan/PycharmProjects/my_cobot_inverse_kinematics/my_cobot.db");
    this->get_parameter("db_path", db_path);
    db_ = std::make_shared<DatabaseManager>("airlab_cobot_connection", QString::fromStdString(db_path));
    joint_state_pub_ =
    this->create_publisher<sensor_msgs::msg::JointState>(
        "joint_states",
        rclcpp::QoS(10)
    );


}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::on_targetButton_clicked()
{
    ui->horizontalSlider->setValue(0);
    ui->verticalSlider->setValue(0);
    ui->verticalSlider_2->setValue(0);
    ui->dial->setValue(0);
    publishJointState({0.0, 0.0, 0.0, 0.0, 0.0, 0.0});
    endEffector.x = endEffector.y = endEffector.z = 0.0f;
    ui->msgText->setPlainText("[>] Reset to home position.");
}


void MainWindow::on_dial_sliderMoved(int position)
{
    float w = static_cast<float>(position - dial_last_pos) * M_PI / 180.0;

    float theta = fmod(atan2(endEffector.y, endEffector.x) + w + M_PI, 2 * M_PI) - M_PI;
    float R = sqrt(endEffector.x * endEffector.x + endEffector.y * endEffector.y);
    float rcos_theta = R * cos(theta);
    float rsin_theta = R * sin(theta);
    endEffector.x = std::clamp(rcos_theta, -ARM_LENGTH, ARM_LENGTH);
    endEffector.y = std::clamp(rsin_theta, -ARM_LENGTH, ARM_LENGTH);

    updateMsg();
    dial_last_pos = position;

}


void MainWindow::on_inputText_returnPressed(){

}


void MainWindow::on_verticalSlider_sliderMoved(int position)
{
    endEffector.set_dy(position);
    updateMsg();

}


void MainWindow::on_horizontalSlider_sliderMoved(int position)
{
    endEffector.set_dx(position);
    updateMsg();

}


void MainWindow::on_verticalSlider_2_sliderMoved(int position)
{

    endEffector.set_dz(position);
    updateMsg();

}




void MainWindow::updateMsg()
{
    // if (std::abs(endEffector.x) <= 0.1 ||
    //     std::abs(endEffector.y) <= 0.1 ||
    //     endEffector.z < 0.0 || endEffector.z > 0.3) {
    //     ui->msgText->setPlainText("[!] Out of range!");
    //     return;
    // }

    QString msg = QString("[>] set (x, y, z) value = (%1, %2, %3)")
        .arg(endEffector.x)
        .arg(endEffector.y)
        .arg(endEffector.z);


    
    auto joints = getJointValuesFromDB();
    if (joints.empty()) {
        ui->msgText->setPlainText("[!] No joint data found for the given end-effector position.");
        return;
    }

    publishJointState(joints);

    ui->msgText->setPlainText(msg);
}


std::array<double, 6> MainWindow::getJointValuesFromDB(){
    auto sqlCmd = QString(R"(
        SELECT j1, j2, j3, j4, j5, j6 FROM joints
        JOIN voxels ON voxel_id = voxels.id
        WHERE
        x >= %1 AND x < %2 AND
        y >= %3 AND y < %4 AND
        z >= %5 AND z < %6
        LIMIT 1        
        )")
        .arg(endEffector.x)
        .arg(endEffector.x + 0.04)
        .arg(endEffector.y)
        .arg(endEffector.y + 0.04)
        .arg(endEffector.z)
        .arg(endEffector.z + 0.04);

    auto result = db_->queryRow(sqlCmd);

    for (int i = 0; i < result.size(); i += 6) {
              // Read raw joint values (already radians)
        std::array<double, 6> joints = {
            result[i + 0].toDouble(),
            result[i + 1].toDouble(),
            result[i + 2].toDouble(),
            result[i + 3].toDouble(),
            result[i + 4].toDouble(),
            result[i + 5].toDouble()
        };
        return joints;
    }

    return {};
}

void MainWindow::publishJointState(const std::array<double, 6>& joint_values)
{
    sensor_msgs::msg::JointState joint_state_msg;
    joint_state_msg.header.stamp = this->now();

    joint_state_msg.name = {
        "joint2_to_joint1",
        "joint3_to_joint2",
        "joint4_to_joint3",
        "joint5_to_joint4",
        "joint6_to_joint5",
        "joint6output_to_joint6"
    };

    joint_state_msg.position.assign(joint_values.begin(), joint_values.end());
    joint_state_msg.velocity = {0.0};
    joint_state_msg.effort.clear();

    joint_state_pub_->publish(joint_state_msg);
}
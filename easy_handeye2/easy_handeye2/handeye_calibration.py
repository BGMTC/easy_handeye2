import os

import rclpy
from rclpy.node import Node
import yaml
from dataclasses import dataclass, asdict

from geometry_msgs.msg import Vector3, Quaternion, Transform, TransformStamped


@dataclass
class HandeyeCalibrationParameters(object):
    name: str
    eye_in_hand: bool
    robot_base_frame: str
    robot_effector_frame: str
    tracking_base_frame: str
    tracking_marker_frame: str
    freehand_robot_movement: bool
    move_group_namespace: str = '/'
    move_group: str = 'manipulator'


class HandeyeCalibrationParametersProvider:
    def __init__(self, node: Node):
        self.node = node
        # declare and read parameters
        self.node.declare_parameter('name')
        self.node.declare_parameter('eye_in_hand')
        self.node.declare_parameter('robot_base_frame')
        self.node.declare_parameter('robot_effector_frame')
        self.node.declare_parameter('tracking_base_frame')
        self.node.declare_parameter('tracking_marker_frame')
        self.node.declare_parameter('freehand_robot_movement')

    def read(self):
        ret = HandeyeCalibrationParameters(
            name=self.node.get_parameter('name').get_parameter_value().string_value,
            eye_in_hand=self.node.get_parameter('eye_in_hand').get_parameter_value().bool_value,
            robot_base_frame=self.node.get_parameter('robot_base_frame').get_parameter_value().string_value,
            robot_effector_frame=self.node.get_parameter('robot_effector_frame').get_parameter_value().string_value,
            tracking_base_frame=self.node.get_parameter('tracking_base_frame').get_parameter_value().string_value,
            tracking_marker_frame=self.node.get_parameter('tracking_marker_frame').get_parameter_value().string_value,
            freehand_robot_movement=self.node.get_parameter('freehand_robot_movement').get_parameter_value().bool_value,
        )
        return ret


class HandeyeCalibration(object):
    """
    Stores parameters and transformation of a hand-eye calibration for publishing.
    """
    DIRECTORY = os.path.expanduser('~/.ros2/easy_handeye')
    """Default directory for calibration yaml files."""

    # TODO: use the HandeyeCalibration message instead, this should be HandeyeCalibrationConversions
    def __init__(self,
                 calibration_parameters=None,
                 transformation=None):
        """
        Creates a HandeyeCalibration object.

        :param transformation: transformation between optical origin and base/tool robot frame as tf tuple
        :type transformation: geometry_msgs.msg.Transform
        :return: a HandeyeCalibration object

        :rtype: easy_handeye.handeye_calibration.HandeyeCalibration
        """
        self.parameters = calibration_parameters

        if transformation is None:
            transformation = Transform()

        self.transformation = TransformStamped(transform=transformation)
        """
        transformation between optical origin and base/tool robot frame

        :type: geometry_msgs.msg.TransformedStamped
        """

        # tf names
        if self.parameters.eye_in_hand:
            self.transformation.header.frame_id = calibration_parameters.robot_effector_frame
        else:
            self.transformation.header.frame_id = calibration_parameters.robot_base_frame
        self.transformation.child_frame_id = calibration_parameters.tracking_base_frame

    @staticmethod
    def to_dict(calibration):
        """
        Returns a dictionary representing this calibration.

        :return: a dictionary representing this calibration.

        :rtype: dict[string, string|dict[string,float]]
        """
        ret = {
            'parameters': asdict(calibration.parameters),
            'transformation': {
                'x': calibration.transformation.transform.translation.x,
                'y': calibration.transformation.transform.translation.y,
                'z': calibration.transformation.transform.translation.z,
                'qx': calibration.transformation.transform.rotation.x,
                'qy': calibration.transformation.transform.rotation.y,
                'qz': calibration.transformation.transform.rotation.z,
                'qw': calibration.transformation.transform.rotation.w
            }
        }

        return ret

    @staticmethod
    def from_dict(in_dict):
        """
        Sets values parsed from a given dictionary.

        :param in_dict: input dictionary.
        :type in_dict: dict[string, string|dict[string,float]]

        :rtype: None
        """
        tr = in_dict['transformation']
        ret = HandeyeCalibration(calibration_parameters=HandeyeCalibrationParameters(**in_dict['parameters']),
                                 transformation=Transform(translation=Vector3(x=tr['x'], y=tr['y'], z=tr['z']),
                                                          rotation=Quaternion(x=tr['qx'], y=tr['qy'], z=tr['qz'],
                                                                              w=tr['qw'])))
        return ret

    @staticmethod
    def to_yaml(calibration):
        """
        Returns a yaml string representing this calibration.

        :return: a yaml string

        :rtype: string
        """
        return yaml.dump(HandeyeCalibration.to_dict(calibration), default_flow_style=False)

    @staticmethod
    def from_yaml(in_yaml):
        """
        Parses a yaml string and sets the contained values in this calibration.

        :param in_yaml: a yaml string
        :rtype: None
        """
        return HandeyeCalibration.from_dict(yaml.safe_load(in_yaml))

    def filename(self):
        raise ValueError('TODO')
        return HandeyeCalibration.filename_for_namespace(self.parameters.name)

    @staticmethod
    def filename_for_namespace(name):
        raise ValueError('TODO')
        return HandeyeCalibration.DIRECTORY + '/' + namespace.rstrip('/').split('/')[-1] + '.yaml'

    @staticmethod
    def to_file(calibration):
        """
        Saves this calibration in a yaml file in the default path.

        The default path consists of the default directory and the namespace the node is running in.

        :rtype: None
        """
        if not os.path.exists(HandeyeCalibration.DIRECTORY):
            os.makedirs(HandeyeCalibration.DIRECTORY)

        with open(calibration.filename(), 'w') as calib_file:
            calib_file.write(HandeyeCalibration.to_yaml(calibration))

    @staticmethod
    def from_file(namespace):
        """
        Parses a yaml file in the default path and sets the contained values in this calibration.

        The default path consists of the default directory and the namespace the node is running in.

        :rtype: HandeyeCalibration
        """

        with open(HandeyeCalibration.filename_for_namespace(namespace)) as calib_file:
            return HandeyeCalibration.from_yaml(calib_file.read())

    @staticmethod
    def from_filename(filename):
        """
        Parses a yaml file at the specified location.

        :rtype: HandeyeCalibration
        """

        with open(filename) as calib_file:
            return HandeyeCalibration.from_yaml(calib_file.read())

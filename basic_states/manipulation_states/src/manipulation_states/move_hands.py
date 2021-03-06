#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sat March 8 19:30:00 2014

@author: Chang Long Zhu
@email: changlongzj@gmail.com
"""


import sys
import actionlib
import rospy
import smach

from sensor_msgs.msg import JointState
from control_msgs.msg import FollowJointTrajectoryGoal, FollowJointTrajectoryAction, FollowJointTrajectoryResult, JointTolerance
from trajectory_msgs.msg import JointTrajectoryPoint
from smach_ros.simple_action_state import SimpleActionState
from move_joints_group import move_joints_group

# Useful dictionary for reading in an human friendly way errors
traj_error_dict = {}
for name in FollowJointTrajectoryResult.__dict__.keys():
    if not name[:1] == '_':
        code = FollowJointTrajectoryResult.__dict__[name]
        traj_error_dict[code] = name
        
class prepare_move_joints_group(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded', 'aborted', 'preempted'])
    def execute(self, userdata):
        rospy.loginfo('Executing Move Hands')
        rospy.sleep(1)
        return 'succeeded'
class create_move_hands_goal(smach.State):
    def __init__(self):
        smach.State.__init__(self, 
                             input_keys=['move_hand_side','move_hand_pose'],
                             output_keys=['standard_error', 'move_joint_group','move_joint_poses', 'move_joint_list'],
                             outcomes=['succeeded', 'aborted', 'preempted'])
    def execute(self, userdata):
        rospy.loginfo('In create_move_hands_goal')
        try:
            userdata.move_joint_group = userdata.move_hand_side + '_hand_controller'
            rospy.loginfo('After setting move_joint_group : ' + userdata.move_hand_side + '_hand_controller')
            move_joint_list = []
            move_joint_list.append('hand_'+userdata.move_hand_side+'_thumb_joint')
            move_joint_list.append('hand_'+userdata.move_hand_side+'_middle_joint')
            #move_joint_list.append('hand_'+userdata.move_hand_side+'_middle_2_joint')
            #move_joint_list.append('hand_'+userdata.move_hand_side+'_middle_3_joint')
            move_joint_list.append('hand_'+userdata.move_hand_side+'_index_joint')
            #move_joint_list.append('hand_'+userdata.move_hand_side+'_index_2_joint')
            #move_joint_list.append('hand_'+userdata.move_hand_side+'_index_3_joint')
            
            rospy.loginfo('Joint List is:: ' + str(move_joint_list))
                       
            userdata.move_joint_list = move_joint_list
            userdata.move_joint_poses = userdata.move_hand_pose
            userdata.standard_error = "Successful at creating move_hand_goal"
            return 'succeeded'
        except ValueError:
            userdata.standard_error = "Error at Move_Hands SM"
            return 'aborted'
            
        
class move_hands(smach.StateMachine):
    
    """
    This SM moves a the HAND group of joints.
    
    Required parameters:
        @param move_joint_group_in: indicates the controller associated with the joints
    
    Optional parameters: None
    
    Output keys:
        @key standard_error: Error 
    
    Input keys:
        @key move_hand_side: indicates the side of the hand
        @key move_hand_pose: indicates poses for the joints to reach : 3 joints [thumb, middle, index]
        
        Joints:
        [0.1, 0.1, 0,1] = Open Hands 

    @Usage: 
        self.move_hand_side_out = "right_hand_controller"
        self.userdata.move_hand_pose = [0.1, 0.1, 0.1]
        userdata.move_hand_side = 'right'
        smach.StateMachine.add('Move_Hands',
                                    move_hands(self.move_hand_side_out),
                                    transitions={'succeeded': 'succeeded','preempted':'preempted', 'aborted':'aborted'})

    """
    def __init__(self, move_joint_group_in):
        smach.StateMachine.__init__(self, outcomes=['succeeded', 'aborted', 'preempted'], 
                                    input_keys=['move_hand_side','move_hand_pose'],
                                    output_keys=['standard_error', 'move_joint_group','move_joint_poses', 'move_joint_list'])
        with self:
            # Preparation of the SM
            smach.StateMachine.add('prepare_move_hands',
                                    prepare_move_joints_group(), 
                                    transitions={'succeeded':'prepare_move_hands_goal', 'preempted':'preempted', 'aborted':'aborted'})
            
            # Preparation of the Goal
            smach.StateMachine.add('prepare_move_hands_goal',
                                    create_move_hands_goal(), 
                                    transitions={'succeeded':'send_move_hands_goal', 'preempted':'preempted', 'aborted':'aborted'})
                
            # Send the goal
            smach.StateMachine.add('send_move_hands_goal', 
                                   move_joints_group(move_joint_group_in),
                                   transitions={'succeeded':'succeeded', 'preempted':'preempted', 'aborted':'aborted'})






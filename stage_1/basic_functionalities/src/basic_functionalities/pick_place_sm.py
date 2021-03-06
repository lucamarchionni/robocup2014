#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Cristina De Saint Germain
@email: crsaintc8@gmail.com

26 Feb 2014
"""

import rospy
import smach
from navigation_states.nav_to_poi import nav_to_poi
from speech_states.say import text_to_say
from object_grasping_states.pick_object_sm import pick_object_sm
from object_grasping_states.place_object_sm import place_object_sm
from geometry_msgs.msg import PoseStamped, Pose, Quaternion, Point, PoseWithCovariance
from std_msgs.msg import Header
from manipulation_states.play_motion_sm import play_motion_sm
from object_states.recognize_object import recognize_object
from hri_states.recognize_object_and_pick import RecObjectAndPick
 
# Some color codes for prints, from http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
ENDC = '\033[0m'
FAIL = '\033[91m'
OKGREEN = '\033[92m'
NUMBER_OF_TRIES = 3


class DummyStateMachine(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','aborted', 'preempted'], 
            input_keys=[], 
            output_keys=[])

    def execute(self, userdata):
        print "Dummy state just to change to other state"  # Don't use prints, use rospy.logXXXX
   
        rospy.sleep(3)
        return 'succeeded'

class prepare_unk_object(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','aborted', 'preempted'], 
            input_keys=['object_position','pose_to_place','nav_to_poi_name'], 
            output_keys=['object_position','pose_to_place', 'nav_to_poi_name'])

    def execute(self, userdata):
        
        userdata.object_position = PoseStamped()
        userdata.object_position.header.frame_id = "base_link"
        userdata.object_position.pose.position.x = 0.5
        userdata.object_position.pose.position.z = 1.0
        userdata.object_position.pose.orientation.w = 1.0
        userdata.pose_to_place = PoseStamped()
        userdata.pose_to_place.header.frame_id = "base_link"
        userdata.pose_to_place.pose.position.x = 0.4
        userdata.pose_to_place.pose.position.z = 0.95
        userdata.pose_to_place.pose.orientation.w = 1.0
        userdata.nav_to_poi_name='waste_bin'
         
        rospy.sleep(5)
        return 'succeeded'

# Class that prepare the value need for nav_to_poi
class prepare_location(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','aborted', 'preempted'], 
            input_keys=[], 
            output_keys=['nav_to_poi_name']) 

    def execute(self,userdata):
        userdata.nav_to_poi_name='pick_and_place'
        return 'succeeded'

class process_place_location(smach.State):
    """"
        Getting the POI name of the "Place" location.
    """
    
    def __init__(self):
        smach.State.__init__(self,
                             outcomes = ['succeeded', 'aborted', 'preempted'], 
                             input_keys = ['object_position','object_detected_name','nav_to_poi_name', 'pose_to_place'], 
                             output_keys = ['nav_to_poi_name','pose_to_place', 'object_position'])
    def execute(self, userdata):
        objectList = rospy.get_param("mmap/object/information")
        foundObject= False
        for key,value in objectList.iteritems():
            if value[1] == userdata.object_detected_name:
                object_class = value[3]
                foundObject = True  
                break    
            
        if foundObject:
            pois = rospy.get_param("/mmap/object/" + object_class)
            userdata.nav_to_poi_name = pois.values().pop()[1]
            
            rospy.logwarn("Info " + str(userdata.object_position))
            rospy.logwarn("Type: " + str(type(userdata.object_position)))
#             p = PoseStamped()
#             p.header.frame_id = userdata.object_position.header.frame_id
#             p.pose.position.x = userdata.object_position.pose.pose.position.x
#             p.pose.position.z = userdata.object_position.pose.pose.position.z
#             p.pose.orientation.w = userdata.object_position.pose.pose.orientation.w
#             userdata.object_position = p
            
            # Prepare the place location
            pois = rospy.get_param("/mmap/place")
            for key,value in pois.iteritems():
                if value[1] == userdata.nav_to_poi_name:
                    userdata.pose_to_place = PoseStamped()
                    userdata.pose_to_place.header.frame_id = "base_link"
                    userdata.pose_to_place.pose.position.x = value[2]
                    userdata.pose_to_place.pose.position.z = value[3]
                    userdata.pose_to_place.pose.orientation.w = value[4]
                    break  

            return 'succeeded'
        
        return 'aborted'
    
class checkLoop(smach.State):
    def __init__(self):
        rospy.loginfo("Entering loop_test")
        smach.State.__init__(self, outcomes=['succeeded','aborted', 'preempted', 'end'], 
                                input_keys=['loop_iterations', 'did_unk'],
                                output_keys=['standard_error', 'loop_iterations', "did_unk"])

    def execute(self, userdata):
        
        if userdata.loop_iterations == NUMBER_OF_TRIES:
            return 'end'
        else:
            rospy.loginfo(userdata.loop_iterations)
            userdata.standard_error='OK'
            userdata.did_unk = True
            userdata.loop_iterations = userdata.loop_iterations + 1
            return 'succeeded'
 
class check_object(smach.State):       
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','aborted', 'preempted'], 
                                input_keys=["did_unk"],
                                output_keys=[])
        
    def execute(self, userdata):
    
        if userdata.did_unk:
            return 'succeeded'
         
        return 'aborted'
    
        
class PickPlaceSM(smach.StateMachine):
    """
    Executes a SM that does the test to pick and place.
    The robot goes to a location and recognize one object.
    It picks the object and goes a location where it will be release. 


    Required parameters:
    No parameters.

    Optional parameters:
    No optional parameters


    No input keys.
    No output keys.
    No io_keys.

    Nothing must be taken into account to use this SM.
    """
    def __init__(self):
        smach.StateMachine.__init__(self, ['succeeded', 'preempted', 'aborted'])

        with self:
            # We must initialize the userdata keys if they are going to be accessed or they won't exist and crash!
            self.userdata.nav_to_poi_name=''
            self.userdata.tts_lang = ''
            self.userdata.tts_wait_before_speak = ''
            self.userdata.tts_text = ''
            self.userdata.loop_iterations = 1
            self.userdata.did_unk = False
            self.userdata.object_name = ['Pringles', 'Barritas']
            
            # Say start Pick and Place
            smach.StateMachine.add(
                 'say_start_pick_place',
                 text_to_say("I'm going to start Pick and Place test"),
                 transitions={'succeeded': 'say_go_location', 'aborted': 'say_go_location'}) 
             
            # Say Going to location
            smach.StateMachine.add(
                 'say_go_location',
                 text_to_say("I'm going to the location where I have to recognize some objects", wait=False),
                 transitions={'succeeded': 'prepare_location', 'aborted': 'prepare_location'}) 
             
            # Prepare the poi for nav_to_poi
            smach.StateMachine.add(
                'prepare_location',
                prepare_location(),
                transitions={'succeeded': 'go_location', 'aborted': 'prepare_location', 
                'preempted': 'preempted'})  
 
            # Go to the location
            smach.StateMachine.add(
                'go_location',
                nav_to_poi(),
                transitions={'succeeded': 'recognize_object_and_pick', 'aborted': 'say_go_location', 
                'preempted': 'preempted'})    
 
            # recognize and pick object if found
            smach.StateMachine.add(
                'recognize_object_and_pick',
                RecObjectAndPick(),
                transitions={'succeeded': 'Process_Place_location', 
                             'fail_grasp':'Process_Place_location',
                             'fail_recognize': 'try_again_recognition'})
            
            # Prepare the place location
            smach.StateMachine.add(
                'Process_Place_location',
                process_place_location(),
                transitions={'succeeded':'say_go_second_location',
                             'aborted':'aborted'})

            # Say start object recognition
#             smach.StateMachine.add(
#                  'say_start_obj_recognition',
#                  text_to_say("I'm going to start the Object recognition process.", wait=False),
#                  transitions={'succeeded': 'object_recognition', 'aborted': 'object_recognition'})
#              
#             # Do object_recognition 
#             smach.StateMachine.add(
#                 'object_recognition',
#                 recognize_object(),
#                 transitions={'succeeded': 'process_object_recognition', 'aborted': 'try_again_recognition', 
#                 'preempted': 'preempted'}) 
#    
#             # Process the objects recognized
#             smach.StateMachine.add(
#                 'process_object_recognition',
#                 process_place_location(),
#                 transitions={'succeeded': 'say_grasp_object', 'aborted': 'say_grasp_object', 
#                 'preempted': 'preempted'}) 
                        
            # We don't recognized the object
            smach.StateMachine.add(
                'try_again_recognition',
                checkLoop(),
                transitions={'succeeded': 'recognize_object_and_pick', 'aborted': 'recognize_object_and_pick', 
                'preempted': 'preempted', 'end':'say_fail_recognize'}) 
        
            # Say fail recognize objects
            smach.StateMachine.add(
                 'say_fail_recognize', 
                 text_to_say("I'm not able to recognized any object. I'm going to search for anything"),
                 transitions={'succeeded': 'prepare_unk_object', 'aborted': 'prepare_unk_object'})
            
            # Prepare goal to pick any object
            smach.StateMachine.add(
                 'prepare_unk_object', 
                 prepare_unk_object(),
                 transitions={'succeeded': 'say_grasp_object', 'aborted': 'say_grasp_object'})
            
            # Say grasp object
            smach.StateMachine.add(
                 'say_grasp_object',
                 text_to_say("I'm going to grasp the object", wait=False),
                 transitions={'succeeded': 'grasp_object', 'aborted': 'grasp_object'})
            
            # Grasp the object
            smach.StateMachine.add(
                'grasp_object',
                pick_object_sm(),
                transitions={'succeeded': 'say_go_second_location', 'aborted': 'home_position', #TODO: Change aborted to try again
                'preempted': 'preempted'})    
             
            # Home position
            smach.StateMachine.add(
                'home_position',
                play_motion_sm('home'),
                transitions={'succeeded': 'say_grasp_object', 'aborted': 'home_position', #TODO: Change aborted to try again
                'preempted': 'preempted'})   
   
            # Say go to second location
            smach.StateMachine.add(
                 'say_go_second_location',
                 text_to_say("I'm going to the location where I should release the object", wait=False),
                 transitions={'succeeded': 'go_second_location', 'aborted': 'go_second_location'})
             
            # Go the location - We need to go to the place to object category, so we assume that the
            # object recognition will init the poi to the object must to go
            smach.StateMachine.add(
                'go_second_location',
                nav_to_poi(),
                transitions={'succeeded': 'say_release_obj', 'aborted': 'say_go_second_location', 
                'preempted': 'preempted'}) 

            # Say release object
            smach.StateMachine.add(
                 'say_release_obj',
                 text_to_say("I'm going to release the object", wait=True),
                 transitions={'succeeded': 'release_object', 'aborted': 'release_object'})
            
            # Check if we pick the know or the unk object
            smach.StateMachine.add(
                'check_place_give',
                check_object(),
                transitions={'succeeded':'release_object', 'aborted':'pregrasp_state', 'preempted':'check_place_give'})
            
            # Release the object
            smach.StateMachine.add(
                'release_object',
                place_object_sm(),
                transitions={'succeeded': 'play_motion_state', 'aborted': 'say_release_obj', 
                'preempted': 'preempted'})     
            
            # Pre-grasp position
            smach.StateMachine.add(
                'pregrasp_state',
                play_motion_sm('pre_grasp', skip_planning=True),
                transitions={'succeeded': 'play_motion_state', 'preempted':'play_motion_state', 
                             'aborted':'pregrasp_state'}) 
            
            # Home position
            smach.StateMachine.add(
                'play_motion_state',
                play_motion_sm('home'),
                transitions={'succeeded': 'say_end_pick_place', 'preempted':'say_end_pick_place', 
                             'aborted':'say_end_pick_place'}) 
            
            # Say end Pick and Place
            smach.StateMachine.add(
                 'say_end_pick_place',
                 text_to_say("I finished the Pick and Place test"),
                 transitions={'succeeded': 'succeeded', 'aborted': 'aborted'})
           


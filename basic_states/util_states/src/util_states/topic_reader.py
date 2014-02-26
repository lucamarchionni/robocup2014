#!/usr/bin/env python

import rospy
import smach

#from global_common import ''preempted'', aborted, preempted, o1, o2, o3, o4
class topic_reader_state(smach.State):
    
    def __init__(self, topic_name, topic_type, topic_time_out):
        smach.State.__init__(self, outcomes=['succeeded', 'preempted', 'aborted'], 
                             output_keys=['topic_output_msg', 'standard_error'])
        self.topic_name = topic_name
        self.topic_type = topic_type
        self.topic_time_out = topic_time_out
    def execute(self, userdata):
        try:
            _topic_info = rospy.wait_for_message(self.topic_name, self.topic_type, self.topic_time_out)
            userdata.topic_output_msg = _topic_info
            userdata.standard_error = "Topic Reader : No Error "
            return 'succeeded'
        except rospy.ROSException:
            userdata.standard_error = "Topic Reader : TimeOut Error"
            return 'aborted'
        
class topic_reader(smach.StateMachine):
    
    def __init__(self, topic_name, topic_type, topic_time_out):
        
        smach.StateMachine.__init__(self, outcomes=['succeeded', 'aborted', 'preempted'], 
                             output_keys=['topic_output_msg', 'standard_error'])
        rospy.init_node("Topic_reader")
        with self:
            smach.StateMachine.add('Topic_reader_state', 
                                   topic_reader_state(topic_name, topic_type, topic_time_out), 
                                   transitions={'succeeded':'succeeded', 'preempted':'preempted', 'aborted':'aborted'})
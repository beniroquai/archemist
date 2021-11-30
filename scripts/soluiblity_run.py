from archemist.processing.prcessor import WorkflowManager
from archemist.util.location import Location
from time import sleep
import rospy

# rospy.init_node("kuka_handler")
# print("kuka_handler running")
wm = WorkflowManager()
wm.initializeWorkflow()
wm.createBatch(1,1,Location(1,7,'/ikaStation/RackHolderFrame'))
# set panda and kuka location
wm.process()
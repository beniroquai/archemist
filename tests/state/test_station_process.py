import unittest
from bson.objectid import ObjectId
from datetime import datetime
from mongoengine import connect
from transitions import State
from archemist.core.state.robot_op import RobotOpDescriptor
from archemist.core.state.station_op import StationOpDescriptor
from archemist.core.state.station_process import StationProcess,ProcessStatus, keyOpDetails
from archemist.core.state.lot import Lot, Batch
from archemist.core.util.location import Location
from archemist.core.util.enums import OpResult

class TestProcess(StationProcess):

    def __init__(self, process_model) -> None:
        super().__init__(process_model)
        
        self.STATES = [State(name='init_state'),
            State(name='prep_state', on_enter='initialise_process_data'), 
            State(name='pickup_batch', on_enter=['request_pickup_batch']),
            State(name='run_op', on_enter=['request_to_run_op']),
            State(name='run_analysis_proc', on_enter=['request_analysis_proc']),
            State(name='final_state')]
        
        self.TRANSITIONS = [
            {'source':'init_state','dest':'prep_state'},
            {'source':'prep_state','dest':'pickup_batch'},
            {'source':'pickup_batch','dest':'run_op', 'conditions':'are_req_robot_ops_completed'},
            {'source':'run_op','dest':'run_analysis_proc', 'conditions':'are_req_station_ops_completed'},
            {'source':'run_analysis_proc','dest':'final_state', 'conditions':'are_req_station_procs_completed'}
        ]


    def initialise_process_data(self):
        self.data['batch_index'] = 0

    def request_pickup_batch(self):
        robot_op = RobotOpDescriptor.from_args()
        self.request_robot_op(robot_op)

    def request_to_run_op(self):
        station_op = self.create_key_op("some_op")
        self.request_station_op(station_op)

    def request_analysis_proc(self):
        station_proc = StationProcess.from_args(self.lot, {})
        self.request_station_process(station_proc)

class StationProcessTest(unittest.TestCase):
    
    def setUp(self):
        self._db_name = 'archemist_test'
        self._client = connect(db=self._db_name, host='mongodb://localhost:27017', alias='archemist_state')

    def  tearDown(self) -> None:
        coll_list = self._client[self._db_name].list_collection_names()
        for coll in coll_list:
            self._client[self._db_name][coll].drop()

    def test_key_op_details_embed_document(self):
        key_op_dict = {
            "name": "some_op",
            "type": "StationOpDescriptor",
            "repeat_for_all_batches": True,
            "parameters": [{"stirring_speed": 200, "duration": 10}]
        }
        key_op_d = keyOpDetails.from_dict(key_op_dict)
        self.assertEqual(key_op_d.op_type, "StationOpDescriptor")
        self.assertTrue(key_op_d.repeat_for_all_batches)
        self.assertTrue(key_op_d.parameters)
        self.assertDictEqual(key_op_d.parameters[0], key_op_dict["parameters"][0])


    def test_station_process_fields(self):
        # construct lot
        batch_1 = Batch.from_args(3, Location(1, 2, "some_frame"))
        batch_2 = Batch.from_args(3, Location(1, 2, "some_frame"))
        lot = Lot.from_args([batch_1, batch_2])
        key_op_dicts_list = [
                {
                    "name": "some_op",
                    "type": "StationOpDescriptor",
                    "repeat_for_all_batches": True,
                    "parameters": None
                }
            ]
        # construct process
        proc = StationProcess.from_args(lot, key_op_dicts_list, processing_slot=1)
        self.assertIsNotNone(proc.object_id)
        self.assertIsNone(proc.requested_by)
        dummy_object_id = ObjectId.from_datetime(datetime.now())
        proc.requested_by = dummy_object_id
        self.assertEqual(proc.requested_by, dummy_object_id)
        self.assertEqual(proc.associated_station, "Station")
        self.assertEqual(proc.status, ProcessStatus.INACTIVE)
        self.assertEqual(proc.m_state, "init_state")
        self.assertEqual(proc.processing_slot, 1)
        proc.processing_slot = 3
        self.assertEqual(proc.processing_slot, 3)

        # test skip fields
        self.assertFalse(proc.skip_robot_ops)
        self.assertFalse(proc.skip_station_ops)
        self.assertFalse(proc.skip_ext_procs)
        
        # test data field
        self.assertEqual(len(proc.data), 0)
        proc.data["rack_index"] = 3
        self.assertEqual(len(proc.data), 1)
        self.assertEqual(proc.data["rack_index"], 3)

        # test lot
        proc_lot  = proc.lot
        self.assertEqual(proc_lot, lot)
        self.assertEqual(proc_lot.num_batches, 2)
        self.assertEqual(proc_lot.batches[0], batch_1)

        # test robot_op fields
        self.assertEqual(len(proc.req_robot_ops), 0)
        self.assertEqual(len(proc.robot_ops_history), 0)
        
        robot_op = RobotOpDescriptor.from_args()
        proc.request_robot_op(robot_op)
        self.assertFalse(proc.are_req_robot_ops_completed())
        self.assertEqual(len(proc.req_robot_ops), 1)
        self.assertEqual(proc.status, ProcessStatus.REQUESTING_ROBOT_OPS)
        proc.switch_to_waiting()
        self.assertEqual(proc.status, ProcessStatus.WAITING_ON_ROBOT_OPS)

        robot_op.complete_op(None, OpResult.SUCCEEDED)
        self.assertTrue(proc.are_req_robot_ops_completed())
        self.assertEqual(len(proc.req_robot_ops), 0)
        self.assertEqual(len(proc.robot_ops_history), 1)
        self.assertEqual(proc.status, ProcessStatus.RUNNING)

        # test station_op fields
        key_op_details = proc.key_ops_dict["some_op"]
        self.assertEqual(key_op_details.op_type, "StationOpDescriptor")
        self.assertEqual(key_op_details.repeat_for_all_batches, True)
        self.assertFalse(key_op_details.parameters)
        self.assertEqual(len(proc.req_station_ops), 0)
        self.assertEqual(len(proc.station_ops_history), 0)
        
        station_op = proc.create_key_op("some_op")
        self.assertIsNotNone(station_op.object_id)
        self.assertIsInstance(station_op, StationOpDescriptor)
        
        proc.request_station_op(station_op)
        self.assertFalse(proc.are_req_station_ops_completed())
        self.assertEqual(len(proc.req_station_ops), 1)
        self.assertEqual(proc.status, ProcessStatus.REQUESTING_STATION_OPS)
        proc.switch_to_waiting()
        self.assertEqual(proc.status, ProcessStatus.WAITING_ON_STATION_OPS)

        station_op.complete_op(OpResult.SUCCEEDED)
        self.assertTrue(proc.are_req_station_ops_completed())
        self.assertEqual(len(proc.req_station_ops), 0)
        self.assertEqual(len(proc.station_ops_history), 1)
        self.assertEqual(proc.status, ProcessStatus.RUNNING)

        # test station_proc fields
        self.assertEqual(len(proc.req_station_procs), 0)
        self.assertEqual(len(proc.station_procs_history), 0)
        
        station_proc = StationProcess.from_args(lot, processing_slot=2)
        proc.request_station_process(station_proc)
        self.assertFalse(proc.are_req_station_procs_completed())
        self.assertEqual(len(proc.req_station_procs), 1)
        self.assertEqual(proc.status, ProcessStatus.REQUESTING_STATION_PROCS)
        proc.switch_to_waiting()
        self.assertEqual(proc.status, ProcessStatus.WAITING_ON_STATION_PROCS)

        station_proc._model_proxy.status = ProcessStatus.FINISHED
        self.assertTrue(proc.are_req_station_procs_completed())
        self.assertEqual(len(proc.req_station_procs), 0)
        self.assertEqual(len(proc.station_procs_history), 1)
        self.assertEqual(proc.status, ProcessStatus.RUNNING)

    def test_station_process_state_machine(self):
        # construct lot
        batch_1 = Batch.from_args(3, Location(1, 2, "some_frame"))
        batch_2 = Batch.from_args(3, Location(1, 2, "some_frame"))
        lot = Lot.from_args([batch_1, batch_2])
        key_op_dicts_list = [
                {
                    "name": "some_op",
                    "type": "StationOpDescriptor",
                    "repeat_for_all_batches": True,
                    "parameters": None
                }
            ]
        # construct process
        proc = TestProcess.from_args(lot, key_op_dicts_list, processing_slot=1)
        self.assertEqual(proc.status, ProcessStatus.INACTIVE)
        self.assertIsNone(proc._state_machine)
        self.assertEqual(proc.m_state, "init_state")

        # tick process
        # transition to prep_state
        proc.tick()
        self.assertEqual(proc.status, ProcessStatus.RUNNING)
        self.assertIsNotNone(proc._state_machine)
        self.assertEqual(proc.m_state, "prep_state")
        self.assertEqual(proc.data["batch_index"], 0)
        self.assertEqual(len(proc.req_robot_ops), 0)

        # transition to pickup_batch
        proc.tick()
        self.assertEqual(proc.status, ProcessStatus.REQUESTING_ROBOT_OPS)
        self.assertEqual(proc.m_state, "pickup_batch")
        self.assertEqual(len(proc.req_robot_ops), 1)

        # no transition
        proc.tick()
        self.assertEqual(proc.status, ProcessStatus.REQUESTING_ROBOT_OPS)
        self.assertEqual(proc.m_state, "pickup_batch")
        self.assertEqual(len(proc.req_robot_ops), 1)

        # transition to run_op
        proc.switch_to_waiting()
        self.assertEqual(proc.status, ProcessStatus.WAITING_ON_ROBOT_OPS)
        robot_op = proc.req_robot_ops[0]
        robot_op.complete_op(None, OpResult.SUCCEEDED)
        proc.tick()
        self.assertEqual(proc.status, ProcessStatus.REQUESTING_STATION_OPS)
        self.assertEqual(len(proc.robot_ops_history), 1)
        self.assertEqual(proc.m_state, "run_op")
        self.assertEqual(len(proc.req_station_ops), 1)

        # transition to run_analysis_proc
        proc.switch_to_waiting()
        self.assertEqual(proc.status, ProcessStatus.WAITING_ON_STATION_OPS)
        station_op = proc.req_station_ops[0]
        station_op.complete_op(OpResult.SUCCEEDED)
        proc.tick()
        self.assertEqual(proc.status, ProcessStatus.REQUESTING_STATION_PROCS)
        self.assertEqual(len(proc.station_ops_history), 1)
        self.assertEqual(proc.m_state, "run_analysis_proc")
        self.assertEqual(len(proc.req_station_procs), 1)

        # no transition
        proc.tick()
        self.assertEqual(proc.status, ProcessStatus.REQUESTING_STATION_PROCS)
        self.assertEqual(proc.m_state, "run_analysis_proc")
        self.assertEqual(len(proc.req_station_procs), 1)

        # transition to final_state
        station_proc = proc.req_station_procs[0]
        station_proc._model_proxy.status = ProcessStatus.FINISHED
        proc.tick()
        self.assertEqual(proc.status, ProcessStatus.FINISHED)
        self.assertEqual(proc.m_state, "final_state")

    def test_station_process_skip_requests(self):
        # construct lot
        batch_1 = Batch.from_args(3, Location(1, 2, "some_frame"))
        batch_2 = Batch.from_args(3, Location(1, 2, "some_frame"))
        lot = Lot.from_args([batch_1, batch_2])
        key_op_dicts_list = [
                {
                    "name": "some_op",
                    "type": "StationOpDescriptor",
                    "repeat_for_all_batches": True,
                    "parameters": None
                }
            ]
        # construct process
        proc = TestProcess.from_args(lot, key_op_dicts_list, processing_slot=1,
                                     skip_robot_ops=True, skip_station_ops=True,
                                      skip_ext_procs=True)
        self.assertEqual(proc.status, ProcessStatus.INACTIVE)
        self.assertIsNone(proc._state_machine)
        self.assertEqual(proc.m_state, "init_state")
        self.assertTrue(proc.skip_robot_ops)
        self.assertTrue(proc.skip_station_ops)
        self.assertTrue(proc.skip_ext_procs)

        # transitions to prep_state
        proc.tick()
        self.assertEqual(proc.status, ProcessStatus.RUNNING)
        self.assertEqual(proc.m_state, "prep_state")

        # transition to pickup_batch
        proc.tick()
        self.assertEqual(proc.status, ProcessStatus.RUNNING)
        self.assertEqual(proc.m_state, "pickup_batch")
        self.assertEqual(len(proc.req_robot_ops), 0)

         # transition to run_op
        proc.tick()
        self.assertEqual(proc.status, ProcessStatus.RUNNING)
        self.assertEqual(proc.m_state, "run_op")
        self.assertEqual(len(proc.req_station_ops), 0)

        # transition to run_analysis_proc
        proc.tick()
        self.assertEqual(proc.status, ProcessStatus.RUNNING)
        self.assertEqual(proc.m_state, "run_analysis_proc")
        self.assertEqual(len(proc.req_station_procs), 0)
        
        # transition to final_state
        proc.tick()
        self.assertEqual(proc.status, ProcessStatus.FINISHED)
        self.assertEqual(proc.m_state, "final_state")

if __name__ == "__main__":
    unittest.main()
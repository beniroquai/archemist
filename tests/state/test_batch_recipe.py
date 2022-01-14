import unittest

from pymongo.message import _batched_op_msg

from archemist.state.stations.ika_place_rct_digital import IKAHeatingOpDescriptor, StationOutputDescriptor, IKAStirringOpDescriptor
from archemist.state.batch import Batch
import yaml

from archemist.util.location import Location

class BatchRecipeTest(unittest.TestCase):
    def test_batch(self):
        recipe_doc = dict()
        with open('resources/testing_recipe.yaml') as fs:
            recipe_doc = yaml.load(fs, Loader=yaml.SafeLoader)
        
        batch = Batch.from_arguments('test',31,recipe_doc,2,Location(1,3,'table_frame'))
        self.assertEqual(batch.id, 31)
        self.assertEqual(batch.location, Location(1,3,'table_frame'))
        batch.location = Location(1,3,'chair_frame')
        self.assertEqual(batch.location, Location(1,3,'chair_frame'))
        
        self.assertEqual(batch.num_samples, 2)
        self.assertFalse(batch.are_all_samples_processed())
        self.assertEqual(len(batch.station_history), 0)
        ''' First operation '''
        # process first sample
        self.assertEqual(batch.current_sample_index, 0)
        ika_op1 = IKAHeatingOpDescriptor({'temperature':50, 'duration':10},StationOutputDescriptor())
        batch.add_station_op_to_current_sample(ika_op1)
        batch.add_material_to_current_sample('heat - 50')
        batch.process_current_sample()
        # process second sample
        self.assertEqual(batch.current_sample_index, 1)
        batch.add_station_op_to_current_sample(ika_op1)
        batch.add_material_to_current_sample('heat - 50')
        batch.process_current_sample()
        self.assertTrue(batch.are_all_samples_processed())
        batch.add_station_stamp('IkaRCTDigital-31')
        self.assertEqual(len(batch.station_history), 1)
        ''' Second operation '''
        batch.reset_samples_processing()
        self.assertFalse(batch.are_all_samples_processed())
        # process first sample
        self.assertEqual(batch.current_sample_index, 0)
        ika_op2 = IKAStirringOpDescriptor({'rpm':50, 'duration':10},StationOutputDescriptor())
        batch.add_station_op_to_current_sample(ika_op2)
        batch.add_material_to_current_sample('rpm - 50')
        batch.process_current_sample()
        # process second sample
        self.assertEqual(batch.current_sample_index, 1)
        batch.add_station_op_to_current_sample(ika_op2)
        batch.add_material_to_current_sample('rpm - 50')
        batch.process_current_sample()
        self.assertTrue(batch.are_all_samples_processed())
        batch.add_station_stamp('IkaRCTDigital-31')
        self.assertEqual(len(batch.station_history), 2)

        samples = batch.get_samples_list()
        self.assertEqual(len(samples), 2)
        self.assertEqual(samples[0].rack_index, 0)
        self.assertFalse(samples[0].capped)
        self.assertEqual(len(samples[0].materials), 2)
        self.assertEqual(samples[0].materials[0], 'heat - 50')
        self.assertEqual(len(samples[0].operation_ops), 2)
        self.assertEqual(samples[0].operation_ops[0].mode, ika_op1.mode)
        self.assertEqual(samples[0].operation_ops[0].set_temperature, ika_op1.set_temperature)
        self.assertEqual(samples[0].operation_ops[0].duration, ika_op1.duration)

    def test_recipe(self):
        recipe_doc = dict()
        with open('resources/testing_recipe.yaml') as fs:
            recipe_doc = yaml.load(fs, Loader=yaml.SafeLoader)
        
        batch = Batch.from_arguments('test',31,recipe_doc,2,Location(1,3,'table_frame'))
        self.assertEqual(batch.recipe.id, 198)
        self.assertEqual(batch.recipe.name, 'test_archemist_recipe')
        self.assertEqual(batch.recipe.liquids[0], 'water')
        self.assertEqual(batch.recipe.solids[0], 'sodium_chloride')
        self.assertEqual(batch.recipe.current_state, 'start')
        self.assertFalse(batch.recipe.is_complete())

        # IKAPlatRCTDigital state
        batch.recipe.advance_state(True)
        self.assertEqual(batch.recipe.current_state, 'IkaPlateRCTDigital.IKAStirringOpDescriptor')
        op1 = batch.recipe.get_current_task_op()
        self.assertEqual(op1.__class__.__name__, 'IKAStirringOpDescriptor')
        self.assertEqual(op1.set_stirring_speed, 200)
        self.assertEqual(op1.duration, 10)
        self.assertFalse(batch.recipe.is_complete())
        # IKAPlatRCTDigital state
        batch.recipe.advance_state(True)
        self.assertEqual(batch.recipe.current_state, 'FisherWeightingStation.FisherWeightStablepDescriptor')
        op2 = batch.recipe.get_current_task_op()
        self.assertEqual(op2.__class__.__name__, 'FisherWeightStablepDescriptor')
        self.assertFalse(batch.recipe.is_complete())
        # end state
        batch.recipe.advance_state(True)
        self.assertTrue(batch.recipe.is_complete())

        

if __name__ == '__main__':
    unittest.main()
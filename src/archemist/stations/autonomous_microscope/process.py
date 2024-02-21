from transitions import Machine
from archemist.core.state.station_process import StationProcess
from .state import AutonomousMicroscopeStation, StartImagingOp

class MicroscopeImagingProcess(StationProcess):
    states = ['start_imaging', 'waiting_for_completion', 'process_results', 'completed']

    def __init__(self, *args, **kwargs):
        super(MicroscopeImagingProcess, self).__init__(*args, **kwargs)
        self.machine = Machine(model=self, states=MicroscopeImagingProcess.states, initial='start_imaging')
        self.machine.add_transition(trigger='start', source='start_imaging', dest='waiting_for_completion', after='execute_start_imaging_op')
        self.machine.add_transition(trigger='check_completion', source='waiting_for_completion', dest='process_results', conditions=['is_imaging_complete'])
        self.machine.add_transition(trigger='finalize', source='process_results', dest='completed')

    def execute_start_imaging_op(self):
        # Code to initiate imaging operation
        pass

    def is_imaging_complete(self):
        # Code to check if imaging is complete
        return True

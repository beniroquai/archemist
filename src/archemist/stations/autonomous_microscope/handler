import requests
from archemist.core.processing.handler import StationOpHandler
from .state import AutonomousMicroscopeStation, StartImagingOp, ImagingResult
from archemist.core.util.enums import OpOutcome
from typing import Tuple, List, Optional

class AutonomousMicroscopeStationHandler(StationOpHandler):
    def execute_op(self):
        current_op = self._station.assigned_op
        if isinstance(current_op, StartImagingOp):
            # Assuming the API endpoint to start imaging is /start and returns a task ID
            response = requests.post("http://microscope.api/start")
            if response.status_code == 200:
                task_id = response.json()['task_id']
                self._station.current_task_id = task_id
                # Store task ID or other relevant info as needed
            else:
                # Handle error or retry logic
                pass

    def is_op_execution_complete(self) -> bool:
        # Assuming the API endpoint to check status is /status and returns a completion flag
        task_id = self._station.current_task_id
        response = requests.get(f"http://microscope.api/status/{task_id}")
        if response.status_code == 200:
            return response.json()['is_complete']
        return False

    def get_op_result(self) -> Tuple[OpOutcome, Optional[List[ImagingResult]]]:
        task_id = self._station.current_task_id
        response = requests.get(f"http://microscope.api/result/{task_id}")
        if response.status_code == 200:
            result_data = response.json()
            imaging_result = ImagingResult.from_args(
                origin_op=self._station.assigned_op.object_id,
                image_url=result_data['image_url'],
                analysis_results=result_data['analysis_results']
            )
            return OpOutcome.SUCCEEDED, [imaging_result]
        return OpOutcome.FAILED, None

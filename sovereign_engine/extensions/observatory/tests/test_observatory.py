import unittest
from unittest.mock import Mock, patch
from sovereign_engine.extensions.observatory import Observatory

class TestObservatory(unittest.TestCase):
    def setUp(self):
        self.obs = Observatory()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('sovereign_engine.extensions.observatory.Observatory._run_kernel_check')
    def test_telemetry_collection(self, mock_check, mock_disk, mock_mem, mock_cpu):
        mock_cpu.return_value = 25.5
        mock_mem.return_value = Mock(percent=65.2)
        mock_disk.return_value = Mock(percent=40.0)
        mock_check.return_value = True
        
        metrics = self.obs.collect_telemetry()
        
        self.assertIn('cpu_percent', metrics)
        self.assertIn('memory_percent', metrics)
        self.assertIn('disk_usage', metrics)
        self.assertEqual(metrics['cpu_percent'], 25.5)
    
    def test_drift_detection(self):
        baseline = {'cpu_percent': 20.0, 'memory_percent': 50.0}
        with patch.object(self.obs, 'collect_telemetry') as mock_collect:
            mock_collect.return_value = {'cpu_percent': 35.0, 'memory_percent': 55.0}
            drift = self.obs.check_drift(baseline)
        
        self.assertIn('cpu_percent', drift)
        self.assertNotIn('memory_percent', drift)  # Only 5% change

if __name__ == '__main__':
    unittest.main()

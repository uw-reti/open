# test_pdsystems.py

import unittest
import numpy as np

from functionsfile import PDSystems

class TestPDSystems(unittest.TestCase):

    def setUp(self):
        """Create a fresh PDSystems object before each test."""
        inputs={}
        inputs["operating_time"]=20
        inputs["commission_time"]=1

        inputs["design_cost"]=1000
        inputs["build_cost"]=2000
        inputs["target_design_cost"] = 1000
        inputs["target_build_cost"] = 2000
        inputs["revenue_per_year"]=100
        inputs["om_per_year"]=50

        inputs["discount_rate"]=0.08
        inputs["contingency"]=0.1
        inputs["profit_margin"]=0.1

        inputs["actual_design_progress"]=[25,50,75,100]
        inputs["actual_build_progress"]=[25,50,75,100]
        inputs["target_design_progress"]=[25,50,75,100]
        inputs["target_build_progress"]=[25,50,75,100]

        inputs["percent_design"]=[0.2,0.8,0,0]
        inputs["percent_build"]=[0.1,0.4,0.5,0]
        inputs["percent_OM_to"]=[0,0,0,1]
        inputs["percent_revenue_to"]=[0,0,0,1]
        self.pd = PDSystems(inputs)

    def tearDown(self):
        """Optional cleanup after each test."""
        pass

    # ------------------------------------------------------------------
    # Example test methods
    # ------------------------------------------------------------------

    def test_completion_index(self):
        # Arrange
        full_progress_array = np.array([0,10,20,100,10,20,50,100])

        # Act
        result = self.pd.completion_index(full_progress_array)

        # Assert
        expected = 3
        self.assertEqual(result, expected)
    
    def test_completion_index_for_non_completion(self):
        # Arrange
        full_progress_array = np.array([0,10,20,30,40,50])

        # Act
        result = self.pd.completion_index(full_progress_array)

        # Assert
        expected = None
        self.assertEqual(result, expected)
    
    def test_build_completion_payout_year(self):
        #Arrange
        #Act
        #actual_build_progress = [25,50,75,100], completes at idx=3
        #actual_design_time = len(actual_design_progress) = 4
        #idx=3, frac= (3+1)/4=1, year_within= ceil(1*actual_build_time)= max(1,4) = 4
        #payout_year = actual_design_time(4) + year_within(4) = 8
        actual_build_progress = np.array([25,50,75,100])
        actual_design_progress = np.array([25,50,75,100])
        actual_design_time = len(actual_design_progress)
        actual_build_time = len(actual_build_progress)
        result = self.pd.build_completion_payout_year(actual_build_progress,actual_design_time,actual_build_time)
        #Assert
        expected = 8
        self.assertEqual(result, expected)
    
    def test_returns_none_of_build_never_completes(self):
        actual_build_progress = np.array([25,50,75])
        actual_design_progress = np.array([25,50,75,100])
        actual_design_time = len(actual_design_progress)
        actual_build_time = len(actual_build_progress)
        result = self.pd.build_completion_payout_year(actual_build_progress,actual_design_time,actual_build_time)
        #Assert
        expected = None
        self.assertEqual(result, expected)

    def test_distribute_progress_costs_land_in_correct_years(self):
        full_progress_array = np.array([50,100])
        result = self.pd.distribute_progress_costs(full_progress_array, phase_cost= 100, phase_start=0,phase_length = 2, shares = {"vendor": 0.5, "AE": 0.5})
        expected = {"vendor": [25.0, 25.0], "AE": [25.0, 25.0]} # delta_cum_progress*phase_cost*share, 0.5 * 100 * 0.5

        self.assertAlmostEqual(result["vendor"][0], expected["vendor"][0])
        self.assertAlmostEqual(result["vendor"][1], expected["vendor"][1])
        self.assertAlmostEqual(result["AE"][0], expected["AE"][0])
        self.assertAlmostEqual(result["AE"][1], expected["AE"][1])
    

    def test_distribute_progress_payments_land_in_correct_years(self):
        full_progress_array = np.array([50,100])
        result = self.pd.distribute_progress_payments(full_progress_array, phase_cost= 100, phase_start=0,phase_length = 2, shares = {"vendor": 0.5, "AE": 0.5})
        expected = {"vendor": [25.0, 25.0], "AE": [25.0, 25.0]} # delta_cum_progress*phase_cost*share, 0.5 * 100 * 0.5

        self.assertAlmostEqual(result["vendor"][0], expected["vendor"][0])
        self.assertAlmostEqual(result["vendor"][1], expected["vendor"][1])
        self.assertAlmostEqual(result["AE"][0], expected["AE"][0])
        self.assertAlmostEqual(result["AE"][1], expected["AE"][1])
    
      #TODO: tests that behavior is as expected
    #def test_project_NPVs_are_same(self):
        #TODO: finish this
        #run all 3 PDSystems models: fixed price, IPD and cost+
        #extract the NPVs for each actor
        #sum them
        #check they are all the same

if __name__ == "__main__":
    unittest.main()
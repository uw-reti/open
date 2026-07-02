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

        inputs["design_cost"]=1
        inputs["build_cost"]=10
        inputs["revenue_per_year"]=2
        inputs["om_per_year"]=1

        inputs["discount_rate"]=0.05
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
        self.setUp()
        full_progress_array = np.array([0,10,20,100,105,100,100])

        # Act
        result = self.pd.completion_index(full_progress_array)

        # Assert
        expected = 3
        self.assertEqual(result, expected)
        
    #TODO: one test per function
    
    #TODO: tests that behavior is as expected
    def test_project_NPVs_are_same(self):
        #TODO: finish this
        self.setUp()
        #run all 3 PDSystems models: fixed price, IPD and cost+
        #extract the NPVs for each actor
        #sum them
        #check they are all the same
        


if __name__ == "__main__":
    unittest.main()
# Markov chain comparison class
# create multiple Markov_learning classes, and conduct comparison

import numpy as np
import Markov_learning as ml
import copy

class Markov_comp(object):
    # attributes
    # it may have multiple Markov_learning objects
    # maximum, 10
    ML=[]
    # how many MLs? for comparison between different evolution schedules.
    num_ML = 0
    # testmode?
    test_mode = 0
    # how many conditions?
    conditions = 0
    # status matrix size
    size = 0
    # current status matrix
    status_t0 = 0
    # total time length
    length = 0
    # matrix for comparison-regression.
    comp_matrix = []


    
    def __init__(self, conditions, size, length, schedules):
        #initialize
        # test mode, if all -1s
        if conditions == -1 & size == -1 & length == -1 & schedules == -1:
            # test mode, as published
            self.conditions = 3
            self.size = 2
            self.num_ML = 2
 #           x = ml.Markov_learning(-1,-1,-1)
#            self.ML.append(x)
#            y = ml.Markov_learning(-2,-2,-2)
#            self.ML.append(y)
            self.ML_test1=copy.copy(ml.Markov_learning(-1,-1,-1))
            self.ML_test2=copy.copy(ml.Markov_learning(-2,-2,-2))
#            self.ML = [ml.Markov_learning(-1,-1,-1),ml.Markov_learning(-2,-2,-2)]
#            self.ML = [ml.Markov_learning() for i in range(2)]
#            self.ML[0] = ml.Markov_learning(-1,-1,-1)
#            self.ML[1] = ml.Markov_learning(-2,-2,-2)
            
            self.test_mode = 1
            self.length = 100
            self.status_t0 = np.zeros((self.size))


    # testmode
    def test1(self):
        if self.test_mode < 1:
            return -1
        self.ML[0].test1()
        

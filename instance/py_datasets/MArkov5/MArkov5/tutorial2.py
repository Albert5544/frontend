# Markov learning tutorial no.2 (simulation 2)
# Han et al. (2016) data. Intervention
# attainable vs. unattainable, non-regular
# 101010101...
# 101001000100001...
# 101000100000100000001...

## Output will be 0.csv to 50.csv containing results from 50 intervention schedules
## Each csv file contains 100 rows (t=0 to t=100)
## 2 columns: Participants/Non-participants at t

import Markov_learning as ml
import numpy as np

# create Markov_learning class
# 3 conditions (att vs. unatt vs. control)
# 2 types of subjects (participating vs. non-participating)
# 100 periods
# 50 different types
Test = ml.Markov_learning(3,2,100,50)

# initialize matrices (see Han et al. (2016) for the matrices)
print(Test.setECM_ratio(0,[[18.0/32.0,4.0/40.0],[14.0/32.0,36.0/40.0]]))
print(Test.setECM_ratio(1,[[30.0/34.0,12.0/33.0],[4.0/34.0,21.0/33.0]]))
print(Test.setECM_ratio(2,[[32.0/45.0,14.0/50.0],[13.0/45.0,36.0/50.0]]))

# inital value setting (t0)
print(Test.set_t0([111,127]))

# set 50 different unregular schedules

for i in range(50):
    nowschedule = np.zeros((100))
    flag = 1
    thisgap = 1
    lasto = 0
    for j in range(100):
        if (flag):
            # it's time to apply intervention, let's set attainable
            nowschedule[j] = 0
            # next, no.
            flag = 0
            lasto = j
            # and gap increase
            thisgap = thisgap + i
        else:
            nowschedule[j] = 2
            # next is the turn?
            if (j+1 == (lasto+thisgap)):
                flag = 1
            # first schedule? then regular
            elif ((i == 0) and ((j % 2)==1)):
                flag = 1
            # second trial?
            elif ((lasto == 0) & j == 1):
                flag = 1
                thisgap = thisgap - 1

    # set schedule
    print(Test.set_schedule(i,nowschedule))
    
    # evolution
    print(Test.evolution_all(i))

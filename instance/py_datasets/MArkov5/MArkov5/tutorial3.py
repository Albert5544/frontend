# Markov learning tutorial no.3 (simulation 3)
# Hypothetical data 

## Output will be 0.csv to 50.csv containing results from 50 intervention schedules
## Each csv file contains 100 rows (t=0 to t=100)
## 3 columns: High/Low/Non-participants at t

import Markov_learning as ml

# create Markov_learning class (Simulation 3)
# 3 conditions (att vs. extraordinary vs. control)
# 3 types of subjects (high vs. low participating vs. non-participating)
# 100 periods
# 50 different type of schedules -> will do regular test (length / 2)
Test = ml.Markov_learning(3,3,100,-1)

# hypothetical ECM
# Attainable/extraordinary/control conditions
print(Test.setECM_ratio(0,[[0.7,0.5,0.1],[0.2,0.3,0.2],[0.1,0.2,0.7]]))
print(Test.setECM_ratio(1,[[0.7,0.3,0.1],[0.2,0.6,0.6],[0.1,0.1,0.3]]))
print(Test.setECM_ratio(2,[[0.3,0.1,0.05],[0.5,0.4,0.15],[0.2,0.5,0.8]]))

# inital value setting (t0)
print(Test.set_t0([100,100,100]))

# we are going to test 50 different intervals with regular interventions
# un attn (condition 0) attanable (condition 1) vs. control (condition 2)
print(Test.set_regular_schedule(0,1))

# create matrices for comparison
# for now, interval = 6 vs. control
# group 0: H 1: L 2: N
print(Test.create_comp_matrix(10,50,0,1))

# conduct t test
print(Test.comp_t_test(0))

# conduct the ttest for all schedules vs. condition
# in this case, will see # of participants
print(Test.comp_all_schedules_t(0,1,0))

# print values (t, uncorr t, corr t, Cohen's D)
print(Test.tresult_regular[:][:])

# conduct regular mixed effects analysis
print(Test.comp_all_schedules_mixed(0,1,0))

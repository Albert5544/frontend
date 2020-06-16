# Markov learning tutorial no.1 (simulation 1)
# Han et al. (2016) data. Intervention
# attainable vs. extraordinary

## Output will be 0.csv to 50.csv containing results from 50 intervention schedules
## Each csv file contains 100 rows (t=0 to t=100)
## 2 columns: Participants/Non-participants at t
## Note: you might see the results from extraordinary vs. control conditions, since this part will be executed at the end.
## thus, the results from attainable vs. control condition will be overwritten.
## If you would like to see the results from attainable vs. control condition, then you might have to remark out the second half of this code.

import Markov_learning as ml

# create Markov_learning class
# 3 conditions (att vs. extraordinary vs. control)
# 2 types of subjects (participating vs. non-participating)
# 100 periods
# 50 different type of schedules -> will do regular test (length / 2)
Test = ml.Markov_learning(3,2,100,-1)

# initialize matrices (see Han et al. (2016) for the matrices)
print(Test.setECM_ratio(0,[[18.0/32.0,4.0/40.0],[14.0/32.0,36.0/40.0]]))
print(Test.setECM_ratio(1,[[30.0/34.0,12.0/33.0],[4.0/34.0,21.0/33.0]]))
print(Test.setECM_ratio(2,[[32.0/45.0,14.0/50.0],[13.0/45.0,36.0/50.0]]))

# inital value setting (t0)
print(Test.set_t0([111,127]))

# we are going to test 50 different intervals with regular interventions
# attanable (condition 0) vs. control (condition 2)
print(Test.set_regular_schedule(0,2))

# create matrices for comparison
# for now, interval = 6 vs. control
print(Test.create_comp_matrix(10,50,0,1))

# conduct t test
print(Test.comp_t_test(0))

# conduct the ttest for all schedules vs. condition
# in this case, will see # of participants
print(Test.comp_all_schedules_t(0,1,0))

# print values (t, uncorr t, corr t, Cohen's D)
print(Test.tresult_regular[:][:])


## Here starts the second half of this simulation
## if you would like to print out csv files from the comparison between
## Attainable vs . control condition, then remark out the rest.
# Another test for the extraordinary condition
Test1 = ml.Markov_learning(3,2,100,-1)

# initialize matrices (see Han et al. (2016) for the matrices)
print(Test1.setECM_ratio(0,[[18.0/32.0,4.0/40.0],[14.0/32.0,36.0/40.0]]))
print(Test1.setECM_ratio(1,[[30.0/34.0,12.0/33.0],[4.0/34.0,21.0/33.0]]))
print(Test1.setECM_ratio(2,[[32.0/45.0,14.0/50.0],[13.0/45.0,36.0/50.0]]))

# inital value setting (t0)
print(Test1.set_t0([111,127]))

# we are going to test 50 different intervals with regular interventions
# extraordinary (condition 1) vs. control (condition 2)
print(Test1.set_regular_schedule(1,2))

# create matrices for comparison
# for now, interval = 6 vs. control
print(Test1.create_comp_matrix(10,50,0,1))

# conduct t test
print(Test1.comp_t_test(0))

# conduct the ttest for all schedules vs. condition
# in this case, will see # of participants
print(Test1.comp_all_schedules_t(0,1,0))

# print values (t, uncorr t, corr t, Cohen's D)
print(Test1.tresult_regular[:][:])

# conduct regular mixed effects analysis
print(Test.comp_all_schedules_mixed(0,1,0))


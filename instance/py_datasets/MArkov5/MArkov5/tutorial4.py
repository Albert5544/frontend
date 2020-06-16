# Markov learning tutorial no.4 (simulation 4)
# Hypothetical data
# attainable vs. unattainable, non-regular
# In this tutorial, test mixed interventions
# schedule 1: attn - extraordinary - cont - attn - extraordinary - cont ...
# schedule 2: extraordinary - attn - cont ...
# schedule 3: attn - attn - cont ...
# schedule 4: extraordinary - extraordinary - cont...
# scheudle 5: cont-....

## Output will be 0.csv to 4.csv containing results from 4 intervention schedules
## Each csv file contains 100 rows (t=0 to t=100)
## 3 columns: High/Low/Non-participants at t


import Markov_learning as ml

# create Markov_learning class (Simulation 4)
# 3 conditions (att vs. extraordinary vs. control)
# 3 types of subjects (high vs. low participating vs. non-participating)
# 100 periods
# 4 different type of schedules 
Test = ml.Markov_learning(3,3,100,5)

# hypothetical ECM
# Attainable/extraordinary/control conditions
print(Test.setECM_ratio(0,[[0.7,0.6,0.1],[0.2,0.3,0.2],[0.1,0.1,0.7]]))
print(Test.setECM_ratio(1,[[0.3,0.2,0.1],[0.6,0.7,0.6],[0.1,0.1,0.3]]))
print(Test.setECM_ratio(2,[[0.3,0.1,0.05],[0.5,0.4,0.15],[0.2,0.5,0.8]]))

# inital value setting (t0)
print(Test.set_t0([1000,1000,1000]))

# enter schedule from 0 to 4 (1 to 5, actually)
print(Test.set_schedule(0,[1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1]))
print(Test.set_schedule(1,[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0]))
print(Test.set_schedule(2,[1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1,1,2,1]))
print(Test.set_schedule(3,[0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0]))
print(Test.set_schedule(4,[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2]))

# do all evolutions
for i in range (5):
    print (Test.evolution_all(i))

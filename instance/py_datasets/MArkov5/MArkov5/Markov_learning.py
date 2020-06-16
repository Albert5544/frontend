"""
Markov learning Class v1.0 (Hyemin Han, Kangwook Lee, & Firat Soylu)
This class was designed to implement Markov learning processes with ECM
"""

# Markov chain learning class
# This class contains ECM and statuses at different ts

import numpy as np
import ECM as em
import pandas as pd
import statsmodels.api as sm
import statsmodels.stats as ss
from scipy.stats.mstats import zscore

class Markov_learning(object):
    """
    Attribute description:
    ECM: contains multiple ECM for pertaining conditions.
    conditions: indicates number of conditions to be implemented by Markov
        learning class
    size: indicates how many participant conditions are available
    status_t0: participant states at t0 (starting point)
    status_t_now: arrays containing participant states at certan ts. They will
        be calculated during evolution processes
    length: how many iterations will occur during evolution processes?
    schedule: arrays containing intervention schedules
    num_schedules: how many intervention schedules will be set?
    comp_evol: arrays indicating whether an evolution process for a certain
        intervention schedule is completed.
    comp_mat: matrices containing participant statuses for statistical
        comparisons.
    comp_mat_data: comp_mat converted into a dataframe.
    comp_done: indicates whether a comparison process is done.
    regular_schedule: indicates whether this class is designated to process and
        test regular (only one type per schedule with a regular interval)
        intervention schedules.
    tgroup1 & 2: data buffers for t-tests.
    tresult: contains results from a t-test.
    tresult_regular: contains multiple results from t-tests between regular
        intervention schedules.
    mixedresult_regular: contains multiple results from mixed effects analyses
        between regular intervention schedules.
    """
    # attributes
    # it has ECM
    ECM = []
    # how many conditions?
    conditions = 0
    # status matrix size
    size = 0
    # current status matrix
    status_t0 = 0
    status_t_now = []
    # intervention schedule
    int_schedule = 0
    # test mode?
    test_mode = 0
    # now time
    t_now = 0
    # total time length
    length = 0
    # intervention schedule
    schedule = []
    # for comparison, number of different schedules
    num_schedules = 0
    # evolution completed?
    comp_evol = []
    # matrix for comparison (x vs y -> 2 schedules)
    comp_mat = []
    # in the form of dataframe
    comp_mat_data = []
    # comparison done?
    comp_done = 0
    # regular vs control condition comparison?
    # if do regular schedule, automatically create schedules (schedules = length/2).
    regular_schedule = 0
    # for t-test
    tgroup1=[]
    tgroup2=[]
    tresult=[]
    # for repeted t-test and mixed effects model analysis (regular test purpose)
    tresult_regular=[]
    mixedresult_regular=[]

    def __init__(self, conditions, size, length, schedules):
        """
        Create Markov learning class
        Requires condition number, participant status number, length of
            intervention schedules, and number of intervention schedules
        Several test modes are activated when all parameters are smaller than 0
        """
        # initialize

        # tresult is always common. [0] t-value [1] p-value [2] Sidak p-value [3] Cohen's D
        self.tresult=np.zeros((4))
        
        # test mode, if conditions == -1 & size == -1
        if conditions == -1 & size == -1 & length == -1 & schedules == -1:
            # test mode, as published
            self.conditions = 3
            self.size = 2
            self.createECM(3,2)
            self.status_t0 = np.zeros((2))
            self.test_mode = 1
            self.schedules = 2
            self.length = 100
            self.status_t_now = np.zeros((self.schedules,self.length,self.size))
            self.schedule = np.zeros((self.schedules,self.length))
            self.comp_evol = np.zeros((self.schedules))
            self.comp_mat = np.zeros((self.length * 2,6))
            self.tgroup1 = np.zeros((self.length))
            self.tgroup2 = np.zeros((self.length))
        # testmode 2 is testing regular condition.
        elif conditions == -2 & size == -2 & length == -2 & schedules == -2:
            self.conditions = 3
            self.size = 2
            self.createECM(3,2)
            self.status_t0 = np.zeros((2))
            self.test_mode = 2
            self.schedules = 0
            self.length = 100
            
  
            self.comp_mat = np.zeros((self.length * 2,6))
            self.tgroup1 = np.zeros((self.length))
            self.tgroup2 = np.zeros((self.length))
        else:
            # set condition number
            self.conditions = conditions
            # set matrix size number
            self.size = size
            # create empty ECMs
            self.createECM (conditions, size)
            # create t0 status
            self.status_t0 = np.zeros((size))
            # not test mode
            self.test_mode = 0
            # time length
            self.length = length
            # how many different schedules will be compared?
            self.schedules = schedules
            
            # schedule == 0, then regular case. If not, then create schedule var.
            if schedules > 0:
                self.schedule = np.zeros((self.schedules,self.length))
                # reset status_t_now and schedule variables per num of set schedules
                self.status_t_now = np.zeros((self.schedules,self.length,self.size))
                self.comp_evol=np.zeros((self.schedules))
            self.comp_mat = np.zeros((self.length*2,6))
            self.tgroup1 = np.zeros((self.length))
            self.tgroup2 = np.zeros((self.length))

    def pooled_sd(self, s1, s2, n1, n2):
        """
        Calculate pooled standard deviation when different two sds (s1 and s2)
            and n sizes (n1 and n2) are given.
        If any parameter is smaller than zero (NaN will be resulted), then
            returns -1 (error)
        If successful, return the calculated pooled sd.
        """
        # Calculate combined pooled SD for Cohen's D calculation
        # should not be 0
        if (s1 <= 0) or (s2 <= 0) or (n1 <= 0) or (n2 <= 0):
            return -1 # error
        sd = np.sqrt( ( (n1-1)*s1*s1+(n2-1)*s2*s2)/(n1+n2-2))
        return sd
            
    def createECM(self,conditions, size):
        """
        Create multiple ECM (number is designated previously, self.conditions
        Check whether condition number is valid (should be >=2)
        If not, returns -1 (error, condition number < 2)
        Check whether the specified size of ECM is not smaller than 2
        If not, returns -2 (error, size < 2)
        If successful, returns 1.
        """
        # create ECM according to the number of conditions
        # if conditions < 2, error
        if conditions < 2:
            return -1

        # if size < 2, error
        if size < 2:
            return -2

        # check creation failure
        flag = 1
        
        # create empty ECMs
        for i in range(conditions):
            x = em.ECM_matrix(i,size)
            self.ECM.append(x)

        # creation was successful
        return 1

    def setECM_ratio(self,cond_num,matvalue):
        """
        Set a certain ECM (cond_num)'s ECM matrix with given matvalue.
        This matvalue should contain values designated in terms of ratio
            describing transitions in participant status between t -> t+1
        cond_num should be within the boundary of self.conditions.
        If not, returns -2 (error, condition number out of boundary)
        The size of matvalue should be consistent with the previously set
            ECM's size.
        If not, then ECM.setmatrix_ratio will return error accordingly,
            returns -10 (error, size does not match)
        If the sum of a certain column in the given matvalue matrix is not 1.0
            then ECM.setmatrix_ratio will return error accordingly,
            returns -11 (error, sum of column != 1.0)
        If successful, returns 1.
        """
        # set a certain ECM(cond_num) by ratio matrix

        # if condition number is out of the current boundary, error
        if (cond_num < 0) or (cond_num >= self.conditions):
            return -2

        # set the current ECM
        success = self.ECM[cond_num].setmatrix_ratio(matvalue)

        return success

    def set_t0(self, t0):
        """
        Set the initial participant states at t0
        The size of t0 should be identical to the status_t0 size (self.size)
        If not, returns -1 (error).
        If successful, returns 1.
        """
        # set initial t0 value
        # if size of t0 is not identical to the size, error.

        if len(t0) != self.size:
            return -1

        # set value
        self.status_t0 = t0
        return 1

    def evol_next(self, num_schedule, condition):
        """
        Perform evolution, from t to t+1, with a certain given preset
            schedule (num_schedule).
        If, num_schedule exceeds preset schedule number, then error.
            returns -1
        If error occurs during ECM.evolution and current t = 0,
            returns -2 (error)
        If error occurs during ECM.evolution and current t > 0,
            returns -3 (error)
        If successful, returns 1
        """
        # is condition out of the boundary?
        if (num_schedule < 0) or (num_schedule >= self.schedules):
            # error
            return -1
        
        # calculate next evol t + 1
        # calculate t+1
        # beginning?
        if self.t_now == 0:
            # first trial
            t_next = self.ECM[condition].evolution_t1(self.status_t0)
            # error occured?
            if t_next == None:
                return -2
            # ok
            for i in range(self.size):
                # for all status labels
                self.status_t_now[num_schedule][self.t_now][i] = t_next[i] 

                
        else:
            # send the current status
            t_next = self.ECM[condition].evolution_t1(self.status_t_now[num_schedule][self.t_now-1])
            # error occured?
            if t_next == None:
                return -3
            # ok
            for i in range(self.size):
                # for all status labels
                self.status_t_now[num_schedule][self.t_now][i] = t_next[i]                                                         
        # t + 1
        self.t_now = self.t_now + 1
        return 1

    def set_schedule(self, num_schedule, schedule):
        """
        Set an intervention schedule, num_schedule.
        If a given schedule number exceeds the limit (self.schedules),
            returns -1 (error, schedule number out of boundary)
        If a given schedule's length does not match with the length of this
            Markov learning class's schedule length (self.length), returns -2
            (error, length does not match)
        If a certain intervention component (i) in a given intervention
            schedule exceeds the preset number of different types of
            intervention conditions (self.conditions), returns -3 (error,
            intervention type number out of boundary)
        If successful, returns 1
        """
        # if num_schedules out of boundary? error
        if (num_schedule < 0) or( num_schedule >= self.schedules):
            return -1
        # set intervention schedule
        # check whether the length of the parameter is identical to the preset length of the class
        if len(schedule) != self.length:
            # not idential = error.
            return -2
        # check whether there is any input out of the boundary of preset condition num.
        for i in range(self.length):
            if schedule[i] >= self.conditions:
                return -3

        # if everything is okay, then set.
        self.schedule[num_schedule] = schedule
        return 1

    def evolution_all(self, num_schedule):
        """
        Perform evolution from t = 0 to self.length for a given intervention
            schedule, num_schedule.
        If num_schedule exceed the current boundary of intervention schedule
            numbers (self.schedules), returns -1 (error)
        If a selected intervention schedule array (self.schedule[num_schedule])
            is empty, returns -2 (error)
        If there is no available schedule, returns -3 (error)
        If self.status_t0, participant states at t0, was not set, returns
            -4 (error)
        If successful, returns 1
        """
        # calculate evolved, predicted values for t1 to t_end

        # if num_schedule is out of boundary,
        if num_schedule >= self.schedules:
            return -1 # error
        # if schedule[num_schedule] is currently empty -> error
        if len(self.schedule[num_schedule]) == 0:
            return -2

        # if current schedule is empty -> error
        if (self.length == 0) or (len(self.schedule) == 0):
            return -3

        # if no current status -> error
        if self.status_t0 == 0:
            return -4

        # clear current t
        self.t_now = 0

        # evolution start
        for i in range(self.length):
            self.evol_next(num_schedule, int(self.schedule[num_schedule][i]))

        # evolution for this schedule completed
        self.comp_evol[num_schedule] = 1

        # comparison not completed
        self.comp_done = 0

        # create csv file containing all the things
        # csv name should be the schedule number.
        output = np.asarray(self.status_t_now[num_schedule])
        np.savetxt("%d.csv" % (num_schedule),output,delimiter=",")
        
        return 1

    def create_comp_matrix(self, schedule1, schedule2, cond1, cond2):
        """
        This method creates a dataset matrix for the comparison between
            results of schedule 1 vs. schedule 2.
        Once evolution processes for both schedules 1 and 2 are completed,
            then create a matrix containing participant statuses at t = 0 to
            self.length situated at cond1 and cond2.
        The created matrix is stored in self.comp_mat.
        If cond1 number is not valid (out of boundary), returns -1 (error)
        If cond2 number is not valid (out of boundary), returns -2 (error)
        If cond1 eq cond2, returns -3 (error, impossible to compare the same
            condition)
        If schedule 1 number is out of boundary, returns -4 (error)
        If schedule 2 number is out of boundary, returns -5 (error)
        If the given two schedule numbers are identical (schedule1 ==
            schedule2), returns -6 (error, impossible to compare the same
            schedule)
        If the evolution process for schedule 1 was not completed, returns -7
            (error, evolution_all should have been done previously).
        If the evolution process for schedule 2 was not completed, returns -8
            (error, evolution_all should have been done previously).
        If successful, returns 1
        """
        
        # comparison between two schedules, two conditions
        # e.g., non-participants vs participants in intervention schedule plan 1 vs plan 2
        # note: all schedule nums and cond nums start from 0, not 1!

        # first, both the condition nums should be in the boundary of size
        # if not, then error
        if (cond1 < 0) or (cond1 >= self.conditions):
            return -1
        elif (cond2 < 0) or (cond2 >= self.conditions):
            return -2
        elif (cond1 == cond2):
            return -3
        # also, schedule numbers should also be in the boundary
        elif (schedule1 <0) or (schedule1>=self.schedules):
            return -4
        elif (schedule2 <0) or (schedule2>=self.schedules):
            return -5
        elif (schedule1 == schedule2):
            return -6
        # evolution completed?
        elif (self.comp_evol[schedule1] == 0):
            return -7
        elif (self.comp_evol[schedule2] == 0):
            return -8

        # now, create the comparison matrix for two conditions
        for i in range(self.length):
            # two items per i (schedule x cond)
            # for schedule 1
            self.comp_mat[i][0] = i
            self.comp_mat[i][1] = 0
            # condition1
            self.comp_mat[i][2] = self.status_t_now[schedule1][i][cond1]
            # condition2
            self.comp_mat[i][3] = self.status_t_now[schedule1][i][cond2]
            # difference and ratio
            self.comp_mat[i][4] = self.comp_mat[i][2]-self.comp_mat[i][3]
            self.comp_mat[i][5] = self.comp_mat[i][2]/self.comp_mat[i][3]
            # for schedule 2
            self.comp_mat[i+self.length][0] = i
            self.comp_mat[i+self.length][1] = 1
            self.comp_mat[i+self.length][2] = self.status_t_now[schedule2][i][cond1]
            self.comp_mat[i+self.length][3] = self.status_t_now[schedule2][i][cond2]
            self.comp_mat[i+self.length][4] = self.comp_mat[i+self.length][2]-self.comp_mat[i][3]
            self.comp_mat[i+self.length][5] = self.comp_mat[i+self.length][2]/self.comp_mat[i][3]       
        # done
        self.comp_done = 1
        return 1

    def comp_mixed(self):
        """
        Performs mixed effects analysis to compare two conditions,
        If comp_mat was not created, returns -1 (error, nothing to analyze)
        If successful, returns 1
        """
        # conduct mixed effects model analysis
        # comp_matrix should exist
        if self.comp_done == 0:
            return -1 # no->error

        # conduct comparison.
        # save result in self.comp_result
        self.comp_mat_data=pd.DataFrame(self.comp_mat,columns=['T','SCH','Y1','Y2','DIFF','RATIO'])
        # statistical analysis for Y1, Y2, Y1-Y2 and Y1/Y2
        self.comp_result_y1 = sm.MixedLM.from_formula("Y1 ~ SCH", self.comp_mat_data,groups=self.comp_mat_data["T"]).fit()
        self.comp_result_y2 = sm.MixedLM.from_formula("Y2 ~ SCH", self.comp_mat_data,groups=self.comp_mat_data["T"]).fit()
        self.comp_result_ydiff = sm.MixedLM.from_formula("DIFF ~ SCH", self.comp_mat_data,groups=self.comp_mat_data["T"]).fit()
        self.comp_result_yratio = sm.MixedLM.from_formula("RATIO~ SCH", self.comp_mat_data,groups=self.comp_mat_data["T"]).fit() 
        return 1
    
    def comp_r_test(cond):
        """
        Regression analysis is not implemented currently. Not for use.
        """
        # instead of t-test, regression. Han et al. (2016)
        # comp_matrix should exist
        if self.comp_done == 0:
            return -1 # no->error

        # one of four conditions, should be
        if (cond < 0) or (cond >4):
            return -2 # no-> error
        
        return 1

    def comp_t_test(self, cond):
        """
        Conduct the t-tests similar to Han et al. (2016)
        Compare the mean participant status number between two conditions.
        Comparison matrix should be created previously.
        If not, returns -1 (error, comp_matrix should exist)
        If condition number (cond) is out of boundary, returns -2 (error)
        Store results in tresult array.
            [0], tvalue
            [1], pvalue
            [2] Sidak's corrected pvalue
            [3] Cohen's D effect size
        If successful, returns 1
        """
        # conduct mixed t-test analysis
        # comp_matrix should exist
        if self.comp_done == 0:
            return -1 # no->error

        # one of four conditions, should be
        if (cond < 0) or (cond >4):
            return -2 # no-> error

        # rearrange array. Make two groups
        for i in range(self.length):
            self.tgroup1[i] = self.comp_mat[i][cond+2]
            self.tgroup2[i] = self.comp_mat[i+self.length][cond+2]

        # conduct comparison.
        tr = ss.weightstats.ttest_ind(self.tgroup1, self.tgroup2, alternative='two-sided')
        # t-value
        self.tresult[0] = tr[0]
        # original p-value (uncorr.)
        self.tresult[1] = tr[1]
        # Sidak's correction
        # if all schedules are compared.
        #self.tresult[2] = 1.0-np.power((1.0-tr[1]),(self.schedules+1.0)*self.schedules/2.0)
        self.tresult[2] = 1.0-np.power((1.0-tr[1]),self.schedules-1.0)
        # Cohen's D calculation
        # pooled d
        pl = self.pooled_sd(np.std(self.tgroup1),np.std(self.tgroup2),len(self.tgroup1),len(self.tgroup2))
        # average and Cohen's D
        self.tresult[3] = (np.average(self.tgroup1)-np.average(self.tgroup2))/pl

        # non-corrected t-test

        # bonferroni's correction.
        # according to the number of total comparisons -> depends on the number of all schedules.
        return 1

    def comp_all_schedules_mixed(self,cond1,cond2, types):
        """
        Perform mixed effects analyses.
        DV: cond1 or cond2 or cond1-cond2 or cond1/cond2
        FE: intervention schedule
        RE: T
        This method can also be conducted with regular intervention schedules.
        If not (self.regular_schedule!=1), returns -1 (error)
        If cond1 is out of boundary (self.size), returns -2 (error)
        If cond2 is out of boundary (self.size), returns -3 (error)
        If resultant report type (types) is out of boundary (< 0 or > 3),
            returns -4 (error)
        If it fails to create comparison matrices (creat_comp_matrix),
            returns -5 (error)
        If any error occurs while performing actual mixed effects analyses,
            returns -6 (error)
        Results are stored in self.mixedresult_regular.
        If successful, returns 1.
        """
        # iterative mixed effects model analysis between two conditions for all schedules
        # e.g., schedule 0 vs. control ... schedule 49 vs. control

        # regular schedules should be set
        if self.regular_schedule != 1:
            # no? error
            return -1

        # also, cond1 and cond2 should be in the range
        if (cond1<0) or (cond1> self.size):
            return -2 # error
        if (cond2<0) or (cond1>self.size):
            return -3 # error

        # type should be 0-3 (y1, y2, y1-y2, y1/y2)
        if (types < 0) or (types >3):
            return -4 # if not, error

        # temporary comparison matrices
        # from 0 to length/2, create comp matrix
        for i in range(self.schedules-1):
            error = self.create_comp_matrix(i,self.schedules-1,cond1,cond2)
            
            # error occured while creating comparison matrices?
            if error < 0:
                return -5

            error = self.comp_mixed()

            # error occured during mixed effects model test?
            if error <0:
                return -6            

            # record result
            # according to the type number
            if types == 0:
                self.mixedresult_regular.append(self.comp_result_y1)
            elif types == 1:
                self.mixedresult_regular.append(self.comp_result_y2)
            elif types == 2:
                self.mixedresult_regular.append(self.comp_result_ydiff)
            else:
                self.mixedresult_regular.append(self.comp_result_yratio)
            
            

            # indicate by which schedule, done
            #print('%d / %d Done\n' % (i+1,self.schedules-1))
            #print(self.tresult)
            
        return 1

    def comp_all_schedules_t(self, cond1, cond2, types):
        """
        Conduct comparisons between all scheduels (only available for regular
            intervention schedules) using t-test.
        E.g., schedule 0 vs. control ... schedule 49 vs. control
        Schedule 50 is preset as a control condition. (regular case)
        If the class is not set to deal with regular schedules, returns -1
            (error)
        If cond1 is out of boundary (self.size), returns -2 (error)
        If cond2 is out of boundary (self.size), returns -3 (error)
        If resultant report type (types) is out of boundary (< 0 or > 3),
            returns -4 (error)
        If it fails to create comparison matrices (creat_comp_matrix),
            returns -5 (error)
        If any error occurs while performing actual t-test,
            returns -6 (error)
        T-test results are stored in tresult_regular
        If successful, returns 1.
        """
        # iterative comparisons between two conditions for all schedules
        # e.g., schedule 0 vs. control ... schedule 49 vs. control

        # regular schedules should be set
        if self.regular_schedule != 1:
            # no? error
            return -1

        # also, cond1 and cond2 should be in the range
        if (cond1<0) or (cond1> self.size):
            return -2 # error
        if (cond2<0) or (cond1>self.size):
            return -3 # error

        # type should be 0-3 (y1, y2, y1-y2, y1/y2)
        if (types < 0) or (types >3):
            return -4 # if not, error

        # from 0 to length/2, create comp matrix
        for i in range(self.schedules-1):
            error = self.create_comp_matrix(i,self.schedules-1,cond1,cond2)
            
            # error occured while creating comparison matrices?
            if error < 0:
                return -5
            
            # conduct comparison
            error = self.comp_t_test(types)

            # error occured during t-test?
            if error <0:
                return -6
            
            # record result
            self.tresult_regular[i]=self.tresult

        return 1

    def comp_all_schedules_r(self, cond1, cond2, types):
        """
        For regular schedule linear regression analyses
        Not yet implemented. Not for use.
        """
        # instead of t-test, conduct linear regression

        # regular schedules should be set
        if self.regular_schedule != 1:
            # no? error
            return -1

        # also, cond1 and cond2 should be in the range
        if (cond1<0) or (cond1> self.size):
            return -2 # error
        if (cond2<0) or (cond1>self.size):
            return -3 # error

        # type should be 0-3 (y1, y2, y1-y2, y1/y2)
        if (types < 0) or (types >3):
            return -4 # if not, error
        return 1

    def set_regular_schedule(self, cond1, cond2):
        """
        Automatically setup regular intervention schedules with previously
            set parameters.
        Required self attributes: self.schedules, self.conditions, etc.
        cond1 = experimental condition, cond2 = control condition.
        Set cond1 schedules with different intervals (no interval to
            self.length / 2)
        If self.schedules > 0, it means this class was not designated to do
            regular schedules, so returns -1 (error)
        If cond1 or cond2 is out of boundary (self.conditions), returns -2
            (error)
        Automatically create self.schedule arrays according to the rule.
        Automatically perform all evolution processes for all schedules.
        If successful, set self.regular_schedule = 1 and returns 1
        """
        
        # setting regular schedule. from freq = 1 to length/2
        # and, consider cond2 as control condition for comparison.

        # if self.schedules = 0, then consider that the user wants to set regular schedules
        # if not, then error
        if self.schedules > 0:
            return -1

        # check the boundary of condition number.
        if (cond1 < 0) or (cond1 >= self.conditions) or (cond2 <  0) or (cond2 >=self.conditions):
            # out of boundary -> error
            return -2

        # initialize schedule list for freq = 1 to length /2
        self.schedules = int(self.length/2)+1 # +1 for control condition
        self.schedule = np.zeros((self.schedules,self.length))
        self.status_t_now = np.zeros((self.schedules,self.length,self.size))
        self.comp_evol=np.zeros((self.schedules))
        
        # fill the gap
        for i in range(self.schedules-1):
            for j in range(self.length):
                # do cond1?
                if ((j) % (i+1)) == 0:
                    # yes. do cond1
                    self.schedule[i][j] = cond1
                else:
                    # no. control intervention.
                    self.schedule[i][j] = cond2

        # last schedule = all control condition.
        for i in range(self.length):
            self.schedule[self.schedules-1][i] = cond2

        # do evolution for all schedules
        for i in range(self.schedules):
            self.evolution_all(i)

        # declare t-test result variable (x length/2)
        self.tresult_regular=np.zeros((self.schedules-1,4))
        # also, mixed effects analysis
 

        # done
        self.regular_schedule = 1
        return 1
    
        # create matrices showing eta2value (or Cohen's D) and p-value between each schedule and control condition
        # similar to the figures demonstrated in Han et al. (2016)
        # two modes: eta squared from mere difference? (Y1-Y2) or ratio? (Y1/Y2)


        """
        Two methods for testing.
        They should not be used for other than programming and debugging purposes
        """

    def test1(self):
        """
        This method should only be used for testing purposes
        """
        # it should be in the test mode
        if self.test_mode != 1:
            return -1

        # initialize matrices
        self.setECM_ratio(0,[[18.0/32.0,4.0/40.0],[14.0/32.0,36.0/40.0]])
        self.setECM_ratio(1,[[30.0/34.0,12.0/33.0],[4.0/34.0,21.0/33.0]])
        self.setECM_ratio(2,[[32.0/45.0,14.0/50.0],[13.0/45.0,36.0/50.0]])

        # set initial t0 status values
        self.set_t0([111, 127])

        # schedule set. frequency of intervention, 1/3
        x = []
        for i in range(self.length):
            if ((i-1) % 3) == 0:
                x.append(0)
            else:
                x.append(2)
        # set schedule
        self.set_schedule(0,x)
        
        # schedule set. control condition
        y = []
        for i in range(self.length):
                y.append(2)

        # set schedule
        self.set_schedule(1,y)

        # start evolution
        self.evolution_all(0)
        self.evolution_all(1)

        # create comparison matrix for test
        result = self.create_comp_matrix(0,1,0,1)
        
        return result


    def test2(self):
        """
        This method should only be used for testing purposes
        """
        # it should be in the test mode
        if self.test_mode != 2:
            return -1

        # initialize matrices
        self.setECM_ratio(0,[[18.0/32.0,4.0/40.0],[14.0/32.0,36.0/40.0]])
        self.setECM_ratio(1,[[30.0/34.0,12.0/33.0],[4.0/34.0,21.0/33.0]])
        self.setECM_ratio(2,[[32.0/45.0,14.0/50.0],[13.0/45.0,36.0/50.0]])
        # set initial t0 status values
        self.set_t0([111, 127])
        # set regular schedule
        self.set_regular_schedule(0,2)
        return 1

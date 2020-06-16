"""
ECM Class v1.0 (Hyemin Han, Kangwook Lee, & Firat Soylu)
This class implements a matrix component in Evolutionary Causality Matricies
"""

# ECM Class
# This class represent one matrix in ECM

import numpy as np

class ECM_matrix(object):

    """
    Attribute description:
    size: size of ECM. (should be greater than 1)
    matrix: actual matrix array variable
    has_value: indicates whether the current ECM is set and ready to go
    """

    # attributes
    # size
    size = 0
    # matrix (2D)
    matrix = 0
    # does currently have any matrix value?
    has_value = 0
    
    def __init__(self, condition, size):
        """
        Create ECM class
        Requires condition number and matrix size as parameters.
        Since multiple intervention conditions can be implemented in Markov
            Learning class, condition number should be specified.
        """
        # initialization
        # at first, condition number and size should be determinded.
        # as a result a size x size matrix is created.
        self.condition = condition
        self.matrix = np.zeros((size,size))
        self.size = size
        self.has_value = 0
        
    def setsize(self,size):
        """
        Reset the matrix size.
        Once ECM class is created with a certain size, this size value can be
            modified with this method.
        It returns 1 when the modification is successful.
        Return value -1 indicates an error (failure).
        """
        # reset the size
        # size should be greater than 1
        if size < 2:
            # failed
            return -1
        self.matrix = np.zeros((size,size))
        self.size = size
        self.has_value = 0
        # size change successful
        return 1

    def setmatrix_ratio(self, matvalue):
        """
        Set the current matrix elements as ratio (0 - 1.0)
        Check whether the new matrix size is identical to preset matrix size.
        If not, returns -10 (error)
        Check whether the sum of each column is 1.0
        If not, setting fails -> returns -11 (error)
        If successful -> returns 1
        matvalue is stored in self.matvalue, and set has_value as 1
        """
        # if the current input value represents ratio (0 - 1.0)
        # first, check the size of the input matrix
        # if it does not fit into the current matrix size, fail
        if (len(self.matrix) != len(matvalue)):
            return -10
        # check whether the sum of each column is 1
        flag = 0
        
        for i in range(self.size):
            col_sum = 0
            for j in range(self.size):
                col_sum = col_sum + matvalue[j][i]

            # equal to 1?
            if (col_sum != 1) and (col_sum != 1.0):
                flag = 1
            if (col_sum == 1.0):
                flag = 0
                
        # if at least the sum of one col is not 1, then error
        if (flag):
            return -11
        
        # if there is no error, then update the matrix
        self.matrix = matvalue
        # now, it has a value
        self.has_value = 1
        return 1

    def setmatrix_rawvalue(self, matvalue):
        """
        Set the current matrix elements as absolute values
        Check whether the new matrix size is identical to preset matrix size.
        If not, returns -10 (error)
        If successful -> returns 1
        matvalue is stored in self.matvalue, and set has_value as 1
        """
        # if the current input value represents ratio (0 - 1.0)
        # first, check the size of the input matrix
        # if it does not fit into the current matrix size, fail
        if (len(self.matrix) != len(matvalue)):
            return -1
        # calculate ratio matrix from raw numbers
        # e.g., a00 = A00 / (A00 + A10)
        col_sum = np.sum(matvalue, axis = 0)
        for i in range(self.size):
            for j in range(self.size):
                self.matrix[i][j] = float(matvalue[i][j]) / float(col_sum[j])
        
        # now, it has a value
        self.has_value = 1
        return 1

    def evolution_t1(self, t0value):
        """
        Conduct evolution with a given t0value.
        The size of t0value should match with the current mat size.
        If not, then returns None (error)
        If successful, then returns the product (current matrix
        (self.matvalue . t0value).
        """
        # evolve for t + 1
        # t0value is the current status

        # sizes (matrix and t0value) should match
        if (len(self.matrix) != len(t0value)):
            return None

        # if match, then calculate the product of two matrices
        return np.dot(self.matrix,t0value)

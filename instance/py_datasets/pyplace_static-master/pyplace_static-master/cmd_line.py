# cmd_line.py :
#       cmd_line_preprocessor -> Takes an input of the user given command line and the folder name which contains the user's scripts and data
#                             -> returns the absolute address of the directory from which the command line has to be run

#       finder                -> Takes a list of absolute paths of directories having the same name and the path given by the user which is relative to the directory name
#                             -> returns the correct absolute path of the directory

# User defined modules
import files_list
import exceptions

# Built in python modules
import re
from pathlib import Path
import os

def finder(ar,l):
    # ar -> list of absolute paths of directories with the same name
    # l  -> rel. path given by user

    str_cat = ''
    location = ''
    path_found = False
    for j in range(1,len(l)):
        str_cat = str_cat +'/' + l[j] # concating rel. path given by user to absolute path of directory to identify the right directory
    for i in ar:
        new_path = i + str_cat
        if(os.path.exists(new_path)):
            if(path_found==False):
                path_found =True
                location = new_path
            else:
                return exceptions.DuplicateError
    if(path_found):
        p  =Path(location)
        return str(p.parent)
    else:
        return exceptions.PathError

def cmd_line_preprocessor(cmd,folder_name):
    # cmd - string containing the user given command line

    Dfdict = files_list.generate_multimap(folder_name) # Dfdict - filename -> file address multi map (ie. one key to many values), default value of Dfdict is [] 
    
    # Convert command line from string format to array format
    arr = cmd.split(' ')
    arr = list(filter(lambda x: x !='', arr)) # remove empty string elements from the array
    
    if(len(arr)<2):
        raise exceptions.invalidCMDError
    else:
        if(arr[0] in ['python','python2','python3']):
            path_of_file_to_be_executed = arr[1]
            
            l = re.split(r'/|\\',path_of_file_to_be_executed) # Paths may contain back slash or forward slash
            #l = path_of_file_to_be_executed.split('/') # Have to check with windows environment later
            
            l = list(filter(lambda x: x !='', l)) # remove empty string elements from the array

            if(len(l)==1): # Directory of execution will be the same location as the executable python file
                ar = Dfdict[l[0]]
                if(len(ar)==1):
                    return str(Path(ar[0]).parent)
                elif(len(ar)==0):
                    raise exceptions.fileNotFoundError
                else: # only file name given by user but there exists two files with same name
                    raise exceptions.DuplicateError
                    # return None # error to be raised
            else:
                ar = Dfdict[l[0]] # The directory of execution will be the parent dir of l[0], ex: python3 code/file.py, the directory containing code is the directory of execution
                if(ar==[]):
                    return exceptions.DirectoryError
                else:
                    return finder(ar,l)
        else:
            raise exceptions.nonPythonError
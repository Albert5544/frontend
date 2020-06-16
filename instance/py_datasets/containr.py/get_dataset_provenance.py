import os
import sys

from Parser import Parser
from ReportGenerator import ReportGenerator


def get_dataset_provenance(direct):
    print("!")
    with open(direct+"/output.txt","w+") as output:
        output.write("0")
        files = os.listdir(direct)
        for f in files:
            if ".py" in f:
                output.write("now run " + f)
                os.system("now run " + f)
                os.system("ls > " + direct + "/output2.txt")
                output.write("1")
                p = Parser(f, "")
                output.write("2")
                r = ReportGenerator()
                output.write("3")
                r.generate_report(p,direct)


if len(sys.argv)>1:
    get_dataset_provenance(sys.argv[1])

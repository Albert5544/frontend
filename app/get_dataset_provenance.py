import os
import sys

from Parser import Parser
from ReportGenerator import ReportGenerator


def get_dataset_provenance(direct):
    files = os.listdir(direct)
    for f in files:
        if ".py" in f:
            with open("output","w+") as output:
             output.write("now run " + f)
            os.system("now run " + f)
            output.write("1")
            p = Parser(f, "")
            output.write("2")
            r = ReportGenerator()
            output.write("3")
            r.generate_report(p)

if len(sys.argv)>1:
    get_dataset_provenance(sys.argv[1])

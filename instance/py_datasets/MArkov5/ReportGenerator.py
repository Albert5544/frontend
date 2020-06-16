import json
import os


class ReportGenerator:

    def generate_report(self, parserlist,target_path):
        pkgs=[]
        scripts=[]
        for parser in parserlist:
            pkgs.append(self.get_pkg_report(parser.get_pkg_info()))
            scripts.append(parser.get_file_info())
        jsontext = {
            "Pyplace Report": {"Modules Depended": (pkgs),
                               "Individual Scripts": (scripts)}}
        with open(os.path.join(target_path,"report.json"), 'w+') as outputfile:
            json.dump(jsontext, outputfile)

        print("HERE IS the output" + str(jsontext))
        return 0

    def get_pkg_report(self, pkg_list):
        pkg_report = []
        for p in pkg_list:
            pkg_report.append({"name": p[0], "version": p[1]})
        return pkg_report

    def get_script_report(self, scipt):
        json_text = {"script " + str(scipt.get_id()) + ", line " + str(scipt.get_line()):
                        {"input files": scipt.get_input_files(), "output files": scipt.get_output_files()}}
        return json_text

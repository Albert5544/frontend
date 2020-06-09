import os
import requests
import cgi
from pathlib import Path
import celery
import files_list
import py2or3
import pathpreprocess
import ast_test

from app import app, db
from celery.exceptions import Ignore
from celery.contrib import rdb

import requests
import json
import re
import os
import shutil
import fnmatch
import pickle
import zipfile
import sys
import subprocess
import docker
import random
import string
import celery
import time
import cgi
import tarfile

import pandas as pd
import numpy as np
from app.Parse import Parser as ProvParser
from urllib.parse import urlparse
from app.models import User, Dataset
from app import app, db
from celery.exceptions import Ignore
from celery.contrib import rdb
from shutil import copy


def clean_up_datasets(dataset_directory):
    # delete any stored data
    try:
        shutil.rmtree(os.path.join(app.instance_path, 'py_datasets', dataset_directory))
    except:
        try:
            os.remove(os.path.join(app.instance_path, 'py_datasets', dataset_directory))
        except:
            pass


def doi_to_directory(doi):
    """Converts a doi string to a more directory-friendly name
    Parameters
    ----------
    doi : string
          doi

    Returns
    -------
    doi : string
          doi with "/" and ":" replaced by "-" and "--" respectively
    """
    return doi.replace("/", "-").replace(":", "--")


def download_dataset(doi, destination, dataverse_key, api_url="https://dataverse.harvard.edu/api/"):
    """Download doi to the destination directory
    Parameters
    ----------
    doi : string
          doi of the dataset to be downloaded
    destination : string
                  path to the destination in which to store the downloaded directory
    dataverse_key : string
                    dataverse api key to use for completing the download
    api_url : string
              URL of the dataverse API to download the dataset from
    Returns
    -------
    bool
    whether the dataset was successfully downloaded to the destination
    """
    api_url = api_url.strip("/")
    # make a new directory to store the dataset
    # (if one doesn't exist)
    if not os.path.exists(destination):
        os.makedirs(destination)

    try:
        # query the dataverse API for all the files in a dataverse
        files = requests.get(api_url + "/datasets/:persistentId",
                             params={"persistentId": doi}) \
            .json()['data']['latestVersion']['files']

    except:
        return False

    # convert DOI into a friendly directory name by replacing slashes and colons
    doi_direct = destination + '/' + doi_to_directory(doi)

    # make a new directory to store the dataset
    if not os.path.exists(doi_direct):
        os.makedirs(doi_direct)
    # for each file result

    for file in files:
        try:
            # parse the filename and fileid
            # filename = file['dataFile']['filename']
            fileid = file['dataFile']['id']
            contentType = file['dataFile']['contentType']

            # query the API for the file contents
            # In Dataverse, tabular data are converted to non-propietary formats for
            # archival purposes. These files we will need to specifically request for
            # the original file because the scripts will break otherwise. If the files
            # have metadata denoting their original file size, they *should* be a file
            # that was changed so we would need to grab the original
            if ("originalFileSize" in file["dataFile"]):
                response = requests.get(api_url + "/access/datafile/" + str(fileid),
                                        params={"format": "original", "key": dataverse_key})
            else:
                response = requests.get(api_url + "/access/datafile/" + str(fileid))

            value, params = cgi.parse_header(response.headers['Content-disposition'])
            if 'filename*' in params:
                filename = params['filename*'].split("'")[-1]
            else:
                filename = params['filename']

            # write the response to correctly-named file in the dataset directory
            with open(doi_direct + "/" + filename, 'wb') as handle:
                handle.write(response.content)
        except:
            return False
    return files


@celery.task(bind=True)
def build_py_image(self, current_user_id, name, preprocess, dataverse_key='', doi='', zip_file='',
                   install_instructions=''):
    ########## GETTING DATA ######################################################################
    # either get the dataset from the .zip file or download it from dataverse
    dataset_dir = ''

    # currently the two methods are zip file or dataverse

    if zip_file:  # if a set of scripts have been uploaded then its converted to a normal zip file format (ie. zip a folder)
        zip_path = os.path.join(app.instance_path, 'py_datasets', zip_file)  # instance_path -> key path in the server
        # unzip the zipped directory and keep the zip file
        with zipfile.ZipFile(zip_path) as zip_ref:
            dir_name = zip_ref.namelist()[0].strip('/')
            zip_ref.extractall(os.path.join(app.instance_path, 'py_datasets', dir_name))

        # find name of unzipped directory
        dataset_dir = os.path.join(app.instance_path, 'py_datasets', dir_name)
        doi = dir_name
    else:
        dataset_dir = os.path.join(app.instance_path, 'py_datasets', doi_to_directory(doi), doi_to_directory(doi))
        success = download_dataset(doi=doi, dataverse_key=dataverse_key,
                                   destination=os.path.join(app.instance_path, 'py_datasets', doi_to_directory(doi)))
        dir_name = doi_to_directory(doi)
        if not success:
            clean_up_datasets(doi_to_directory(doi))
            return {'current': 100, 'total': 100, 'status': ['Data download error.',
                                                             [['Download error',
                                                               'There was a problem downloading your data from ' + \
                                                               'Dataverse. Please make sure the DOI is correct.']]]}

    pyfiles = files_list.generate_set(dataset_dir)
    py2 = False
    if preprocess:
        try:
            self.update_state(state='PROGRESS', meta={'current': 1, 'total': 5,
                                                      'status': 'Preprocessing files for errors and ' + \
                                                                'collecting provenance data... ' + \
                                                                '(This may take several minutes or longer,' + \
                                                                ' depending on the complexity of your scripts)'})

            # iterate through list of all python files to figure out if its python2 or python3
            hash = files_list.generate_multimap(dataset_dir)
            for file in pyfiles:
                pathpreprocess.path_preprocess(file, dataset_dir, hash)
        except:
            pass

    user_defined_modules = files_list.generate_modules(dataset_dir)

    unknown_pkgs = set()
    docker_pkgs = set()
    pkgs_to_ask_user = set()

    for file in pyfiles:
        py3 = py2or3.python2or3(file)
        (unknown, dockerpkg) = ast_test.get_imports(file, dir_name, user_defined_modules)
        unknown_pkgs = unknown_pkgs.union(unknown)
        docker_pkgs = docker_pkgs.union(dockerpkg)
        if (py3 == False):
            py2 = True

    # Frontend not yet developed part
    for pkgs in unknown_pkgs:
        if not (pkgs in pkg_dict):
            pkgs_to_ask_user.add(pkgs)

    if (len(pkgs_to_ask_user) != 0):
        missing_modules = ''
        for pkg in pkgs_to_ask_user:
            missing_modules += pkg + ','
        return {'current': 100, 'total': 100, 'status': ['Modules not found.',
                                                         [[
                                                              'Kindly mention the pypi package name of these unknown modules or upload these missing modules',
                                                              missing_modules[:-1]]]]}

    # If even a single file contains python2 specific code then we take the entire dataset to be of python2
    if (py2):
        py3 = False

    for p in pyfiles:
        error, err_mesg = pylint_parse.pylint_parser(path, py3)
        if (error):
            p_obj = Path(p)
            return {'current': 100, 'total': 100, 'status': ['Error in code.',
                                                             [['Error identified by static analysis of ' + p_obj.name,
                                                               err_mesg]]]}

    # Albert's part

    # Write the Dockerfile
    # 1.) First install system requirements, this will allow R packages to install with no errors (hopefully)
    # 2.) Install R packages
    # 3.) Add the analysis folder
    # 4.) Copy in the scripts that run the analysis
    # 5.) Change pemissions, containers have had issues with correct permissions previously
    # 6.) Run analyses
    # 7.) Collect installed packages for report
    with open('Dockerfile', 'w+') as new_docker:
        if py2:
            new_docker.write('FROM python: 2\n')
        else:
            new_docker.write('FROM python: 3\n')
        new_docker.write('WORKDIR /home/py_datasets/' + dir_name + ' \n')
        new_docker.write('ADD ' + dir_name + ' /home/py_datasets/' + dir_name + '\n')

        new_docker.write('COPY get_prov_for_doi.sh /home/py_datasets/\n')
        new_docker.write('COPY get_dataset_provenance.py /home/py_datasets/\n')
        new_docker.write('COPY Parser.py /home/py_datasets/\n')
        new_docker.write('COPY ReportGenerator.py /home/py_datasets/\n')

        new_docker.write('RUN chmod a+rwx -R /home/py_datasets/' + dir_name + '\n')
        # used_packages = report["py_datasets Report"]["Modules Depended"]
        new_docker.write('RUN pip install noworkflow[all]\n')

        if docker_pkgs:
            for module in moudle_list:
                new_docker.write(self.build_docker_package_install(module["name"], module["version"]))

        new_docker.write("RUN /home/py_datasets/get_prov_for_doi.sh " \
                         + "/home/py_datasets/" + dir_name + " /home/py_datasets/get_dataset_provenance.py\n")

        d = DockerImageBuilder()
        d.buildImage("/home/py_datasets/" + dir_name)

    # create docker client instance
    client = docker.from_env()
    # build a docker image using docker file
    client.login(os.environ.get('DOCKER_USERNAME'), os.environ.get('DOCKER_PASSWORD'))
    # name for docker image
    current_user_obj = User.query.get(current_user_id)
    # image_name = ''.join(random.choice(string.ascii_lowercase) for _ in range(5))
    image_name = current_user_obj.username + '-' + name
    repo_name = os.environ.get('DOCKER_REPO') + '/'

    client.images.build(path=docker_file_dir, tag=repo_name + image_name)

    self.update_state(state='PROGRESS', meta={'current': 4, 'total': 5,
                                              'status': 'Collecting container environment information... '})

    ########## Generate Report About Build Process ##########################################################
    # The report will have various information from the creation of the container
    # for the user
    report = {}
    report["Container Report"] = {}
    report["Individual Scripts"] = {}

    # There is provenance and other information from the analyses in the container.
    # to get it we need to run the container
    container = client.containers.run(image=repo_name + image_name, \
                                      environment=["PASSWORD=" + repo_name + image_name], detach=True)

    # Grab the files from inside the container and the filter to just JSON files
    prov_files = container.exec_run("ls /home/py_datasets/" + dir_name)[1].decode().split("\n")
    json_files = [prov_file for prov_file in prov_files if ".json" in prov_file]

    # Each json file will represent one execution so we need to grab the information from each.
    # Begin populating the report with information from the analysis and scripts
    container_packages = []
    for json_file in json_files:
        report["Individual Scripts"][json_file] = {}
        # prov_from_container = container.exec_run("cat /home/py_datasets/" +dir_name+ "/prov_data/" + json_file)[1].decode()
        # prov_from_container = ProvParser(prov_from_container, isFile=False)
        # container_packages += get_pkgs_from_prov_json(prov_from_container)
        report["Individual Scripts"][json_file]["Input Files"] = list(
            set(prov_from_container.getInputFiles()["name"].values.tolist()))
        report["Individual Scripts"][json_file]["Output Files"] = list(
            set(prov_from_container.getOutputFiles()["name"].values.tolist()))
    container_packages = list(set([package[0] for package in container_packages]))

    # There should be a file written to the container's system that
    # lists the installed packages from when the analyses were run
    installed_packages = container.exec_run("cat listOfPackages.txt")[1].decode().split("\n")

    # The run log will show us any errors in execution
    # this will be used after report generation to check for errors when the script was
    # run inside the container
    # run_log_path_in_container = "/home/py_datasets/" + dir_name + "/prov_data/run_log.csv"
    # run_log_from_container = container.exec_run("cat " + run_log_path_in_container)

    # information from the container is no longer needed
    container.kill()

    # Finish out report generation
    report["Container Report"]["Installed Packages"] = installed_packages
    report["Container Report"][
        "Packages Called In Analysis"] = container_packages  # [list(package_pair) for package_pair in container_packages]
    report["Container Report"]["System Dependencies Installed"] = sysreqs[0].split(" ")

    # Note any missing packages
    missing_packages = []
    for package in used_packages:
        if package[0] not in installed_packages:
            missing_packages.append(package[0])

    # Error if a package or more is missing
    if (len(missing_packages) > 0):
        print(missing_packages, file=sys.stderr)
        error_message = "ContainR could not correctly install all the packages used in the upload inside of the container. " + \
                        "Docker container could not correctly be created." + \
                        "Missing packages are: " + " ".join(missing_packages)
        clean_up_datasets(dir_name)
        return {'current': 100, 'total': 100, 'status': ['Docker Build Error.',
                                                         [['Could not install R package',
                                                           error_message]]]}

    # run_log_path = os.path.join(app.instance_path, 'py_datasetss', dir_name, "run_log.csv")
    #
    # with open(run_log_path, 'wb') as f:
    #     f.write(run_log_from_container[1])
    #
    # if not os.path.exists(run_log_path):
    #     print(run_log_path, file=sys.stderr)
    #     error_message = "ContainR could not locate any .R files to collect provenance for. " +\
    #                     "Please ensure that .R files to load dependencies for are placed in the " +\
    #                     "top-level directory."
    #     clean_up_datasets(dir_name)
    #     return {'current': 100, 'total': 100, 'status': ['Provenance collection error.',
    #                                                      [['Could not locate .R files',
    #                                                        error_message]]]}

    # check the execution log for errorsr
    errors_present, error_list, my_file = checkLogForErrors(run_log_path)

    if errors_present:
        clean_up_datasets()
        return {'current': 100, 'total': 100,
                'status': ['Provenance collection error while executing inside container.',
                           error_list]}

    ########## PUSHING IMG ######################################################################
    self.update_state(state='PROGRESS', meta={'current': 4, 'total': 5,
                                              'status': 'Pushing Docker image to Dockerhub... '})

    print(client.images.push(repository=repo_name + image_name), file=sys.stderr)

    ########## UPDATING DB ######################################################################

    # add dataset to database
    new_dataset = Dataset(url="https://hub.docker.com/r/" + repo_name + image_name + "/",
                          author=current_user_obj,
                          name=name,
                          report=report)
    db.session.add(new_dataset)
    db.session.commit()

    ########## CLEANING UP ######################################################################

    clean_up_datasets()
    print("Returning")
    return {'current': 5, 'total': 5,
            'status': 'containR has finished! Your new image is accessible from the home page.',
            'result': 42, 'errors': 'No errors!'}

    # more to be added


def build_docker_package_install(self, module, version):
    if version is not None:
        return "RUN pip install " + module + "==" + version + "\n"


def build_image(self, current_user_id, name, preprocess, dataverse_key='', doi='', zip_file='',
                install_instructions=''):
    """Build a docker image for a user-provided dataset
    Parameters
    ----------
    current_user_id : int
                      id of current user
    name : string
           name of the image
    preprocess : bool
                 whether to preprocess the code in the dataset
    dataverse_key : string
                    API key for a dataverse instance
    doi : string
          DOI of the dataset if retrieving dataset from dataverse
    zip_file : string
               name of the .zip file if dataset uploaded as a .zip
    install_instructions : string
                a json encoded as string that contains special instructions for package installation
    """
    ########## GETTING DATA ######################################################################
    # either get the dataset from the .zip file or download it from dataverse
    dataset_dir = ''

    # in case the user provided specific instructions for installing certain packages
    special_packages = None
    if (install_instructions is not ''):
        special_install = json.loads(install_instructions)
        special_packages = [special_install[key][0] for key in special_install.keys()]

    if zip_file:
        # assemble path to zip_file
        zip_path = os.path.join(app.instance_path, 'r_datasets', zip_file)
        # unzip the zipped directory and remove zip file
        with zipfile.ZipFile(zip_path) as zip_ref:
            dir_name = zip_ref.namelist()[0].strip('/')
            zip_ref.extractall(os.path.join(app.instance_path, 'r_datasets', dir_name))
        os.remove(os.path.join(app.instance_path, 'r_datasets', zip_file))
        # find name of unzipped directory
        dataset_dir = os.path.join(app.instance_path, 'r_datasets', dir_name, dir_name)
        doi = dir_name
    else:
        dataset_dir = os.path.join(app.instance_path, 'r_datasets', doi_to_directory(doi),
                                   doi_to_directory(doi))
        success = download_dataset(doi=doi, dataverse_key=dataverse_key,
                                   destination=os.path.join(app.instance_path, 'r_datasets',
                                                            doi_to_directory(doi)))
        if not success:
            clean_up_datasets()
            return {'current': 100, 'total': 100, 'status': ['Data download error.',
                                                             [['Download error',
                                                               'There was a problem downloading your data from ' + \
                                                               'Dataverse. Please make sure the DOI is correct.']]]}
    # print(dataset_dir, file=sys.stderr)

    ########## GETTING PROV ######################################################################

    # run the R code and collect errors (if any)
    if preprocess:
        try:
            self.update_state(state='PROGRESS', meta={'current': 1, 'total': 5,
                                                      'status': 'Preprocessing files for errors and ' + \
                                                                'collecting provenance data... ' + \
                                                                '(This may take several minutes or longer,' + \
                                                                ' depending on the complexity of your scripts)'})
            subprocess.run(['bash', 'app/get_prov_for_doi_preproc.sh', dataset_dir])

            replace_files_with_preproc(dataset_dir, "r")
            replace_files_with_preproc(os.path.join(dataset_dir, 'prov_data'), "json")
        except:
            clean_up_datasets()
    else:
        self.update_state(state='PROGRESS', meta={'current': 1, 'total': 5,
                                                  'status': 'Collecting provenance data... ' + \
                                                            '(This may take several minutes or longer,' + \
                                                            ' depending on the complexity of your scripts)'})
        subprocess.run(['bash', 'app/get_prov_for_doi.sh', dataset_dir, "app/get_dataset_provenance.R"])

    ########## CHECKING FOR PROV ERRORS ##########################################################
    # make sure an execution log exists

    # run_log_path = os.path.join(dataset_dir, 'prov_data', 'run_log.csv')
    # if not os.path.exists(run_log_path):
    #     print(run_log_path, file=sys.stderr)
    #     error_message = "ContainR could not locate any .R files to collect provenance for. " +\
    #                     "Please ensure that .R files to load dependencies for are placed in the " +\
    #                     "top-level directory."
    #     clean_up_datasets()
    #     return {'current': 100, 'total': 100, 'status': ['Provenance collection error.',
    #                                                      [['Could not locate .R files',
    #                                                        error_message]]]}
    #
    # # check the execution log for errors
    # errors_present, error_list, my_file = checkLogForErrors(run_log_path)
    #
    # if errors_present:
    #     clean_up_datasets()
    #     return {'current': 100, 'total': 100, 'status': ['Provenance collection error.',
    #                                                      error_list]}

    ########## PARSING PROV ######################################################################

    self.update_state(state='PROGRESS', meta={'current': 2, 'total': 5,
                                              'status': 'Parsing provenance data... '})
    # build dockerfile from provenance
    # get list of json provenance files
    prov_jsons = [my_file for my_file in os.listdir(os.path.join(dataset_dir, 'prov_data')) \
                  if my_file.endswith('.json')]

    used_packages = []

    # assemble a set of packages used
    for prov_json in prov_jsons:
        print(prov_json, file=sys.stderr)
        used_packages += get_pkgs_from_prov_json( \
            ProvParser(os.path.join(dataset_dir, 'prov_data', prov_json)))

    print(used_packages, file=sys.stderr)
    docker_file_dir = os.path.join(app.instance_path,
                                   'r_datasets', doi_to_directory(doi))
    try:
        os.makedirs(docker_file_dir)
    except:
        pass

    ##### EVERYTHING BEFORE HERE ---> Static analysis? #########
    # Variable Information from containR needed for build process:
    # docker_file_dir is where the Dockerfile will be written to
    # dataset_dir is a directory in the docker_file_dir named after the dataset.
    # used_packages contains a list of tuples. Each tuple is a package AND its version
    # doi is the dataverse doi if that was the provided dataset, OR a dataset name if it was uploaded
    # current_user_id is the user's ID in the database
    # name is what the user chose to be the name of the image, although their user name will be appended to the front
    ########## BUILDING DOCKER ###################################################################

    self.update_state(state='PROGRESS', meta={'current': 3, 'total': 5,
                                              'status': 'Building Docker image... '})

    # copy relevant packages, system requirements, and directory
    sysreqs = []
    with open(os.path.join(dataset_dir, 'prov_data', "sysreqs.txt")) as reqs:
        sysreqs = reqs.readlines()
    shutil.rmtree(os.path.join(dataset_dir, 'prov_data'))

    # Write the Dockerfile
    # 1.) First install system requirements, this will allow R packages to install with no errors (hopefully)
    # 2.) Install R packages
    # 3.) Add the analysis folder
    # 4.) Copy in the scripts that run the analysis
    # 5.) Change pemissions, containers have had issues with correct permissions previously
    # 6.) Run analyses
    # 7.) Collect installed packages for report
    with open(os.path.join(docker_file_dir, 'Dockerfile'), 'w') as new_docker:
        new_docker.write('FROM rocker/tidyverse:3.6.3\n')
        if (len(sysreqs) == 1):
            sysinstall = "RUN export DEBIAN_FRONTEND=noninteractive; apt-get -y update && apt-get install -y "
            new_docker.write(sysinstall + sysreqs[0])
        used_packages = list(set(used_packages))
        if used_packages:
            for package, version in used_packages:
                if (package not in special_packages):
                    new_docker.write(build_docker_package_install(package, version))

        if special_packages:
            for key in special_install.keys():
                instruction = 'RUN R -e \"require(\'devtools\');' + special_install[key][1] + '"\n'
                new_docker.write(instruction)

        # copy the new directory and change permissions
        new_docker.write('ADD ' + doi_to_directory(doi) \
                         + ' /home/rstudio/' + doi_to_directory(doi) + '\n')

        copy("app/get_prov_for_doi.sh", "instance/r_datasets/" + doi_to_directory(doi))
        copy("app/get_dataset_provenance.R", "instance/r_datasets/" + doi_to_directory(doi))
        new_docker.write('COPY get_prov_for_doi.sh /home/rstudio/\n')
        new_docker.write('COPY get_dataset_provenance.R /home/rstudio/\n')

        new_docker.write('RUN chmod a+rwx -R /home/rstudio/' + doi_to_directory(doi) + '\n')
        new_docker.write("RUN /home/rstudio/get_prov_for_doi.sh " \
                         + "/home/rstudio/" + doi_to_directory(doi) + " /home/rstudio/get_dataset_provenance.R\n")
        new_docker.write("RUN R -e 'write(paste(as.data.frame(installed.packages()," \
                         + "stringsAsFactors = F)$Package, collapse =\"\\n\"), \"./listOfPackages.txt\")'\n")

    # create docker client instance
    client = docker.from_env()
    # build a docker image using docker file
    client.login(os.environ.get('DOCKER_USERNAME'), os.environ.get('DOCKER_PASSWORD'))
    # name for docker image
    current_user_obj = User.query.get(current_user_id)
    # image_name = ''.join(random.choice(string.ascii_lowercase) for _ in range(5))
    image_name = current_user_obj.username + '-' + name
    repo_name = os.environ.get('DOCKER_REPO') + '/'

    client.images.build(path=docker_file_dir, tag=repo_name + image_name)

    self.update_state(state='PROGRESS', meta={'current': 4, 'total': 5,
                                              'status': 'Collecting container environment information... '})

    ########## Generate Report About Build Process ##########################################################
    # The report will have various information from the creation of the container
    # for the user
    report = {}
    report["Container Report"] = {}
    report["Individual Scripts"] = {}

    # There is provenance and other information from the analyses in the container.
    # to get it we need to run the container
    container = client.containers.run(image=repo_name + image_name, \
                                      environment=["PASSWORD=" + repo_name + image_name], detach=True)

    # Grab the files from inside the container and the filter to just JSON files
    prov_files = container.exec_run("ls /home/rstudio/" + doi_to_directory(doi) + "/prov_data")[1].decode().split("\n")
    json_files = [prov_file for prov_file in prov_files if ".json" in prov_file]

    # Each json file will represent one execution so we need to grab the information from each.
    # Begin populating the report with information from the analysis and scripts
    container_packages = []
    for json_file in json_files:
        report["Individual Scripts"][json_file] = {}
        prov_from_container = \
        container.exec_run("cat /home/rstudio/" + doi_to_directory(doi) + "/prov_data/" + json_file)[1].decode()
        prov_from_container = ProvParser(prov_from_container, isFile=False)
        container_packages += get_pkgs_from_prov_json(prov_from_container)
        report["Individual Scripts"][json_file]["Input Files"] = list(
            set(prov_from_container.getInputFiles()["name"].values.tolist()))
        report["Individual Scripts"][json_file]["Output Files"] = list(
            set(prov_from_container.getOutputFiles()["name"].values.tolist()))
    container_packages = list(set([package[0] for package in container_packages]))

    # There should be a file written to the container's system that
    # lists the installed packages from when the analyses were run
    installed_packages = container.exec_run("cat listOfPackages.txt")[1].decode().split("\n")

    # The run log will show us any errors in execution
    # this will be used after report generation to check for errors when the script was
    # run inside the container
    run_log_path_in_container = "/home/rstudio/" + doi_to_directory(doi) + "/prov_data/run_log.csv"
    run_log_from_container = container.exec_run("cat " + run_log_path_in_container)

    # information from the container is no longer needed
    container.kill()

    # Finish out report generation
    report["Container Report"]["Installed Packages"] = installed_packages
    report["Container Report"][
        "Packages Called In Analysis"] = container_packages  # [list(package_pair) for package_pair in container_packages]
    report["Container Report"]["System Dependencies Installed"] = sysreqs[0].split(" ")

    # Note any missing packages
    missing_packages = []
    for package in used_packages:
        if package[0] not in installed_packages:
            missing_packages.append(package[0])

    # Error if a package or more is missing
    if (len(missing_packages) > 0):
        print(missing_packages, file=sys.stderr)
        error_message = "ContainR could not correctly install all the R packages used in the upload inside of the container. " + \
                        "Docker container could not correctly be created." + \
                        "Missing packages are: " + " ".join(missing_packages)
        clean_up_datasets()
        return {'current': 100, 'total': 100, 'status': ['Docker Build Error.',
                                                         [['Could not install R package',
                                                           error_message]]]}

    run_log_path = os.path.join(app.instance_path, 'r_datasets', doi_to_directory(doi), "run_log.csv")

    # with open(run_log_path, 'wb') as f:
    #     f.write(run_log_from_container[1])

    # if not os.path.exists(run_log_path):
    #     print(run_log_path, file=sys.stderr)
    #     error_message = "ContainR could not locate any .R files to collect provenance for. " +\
    #                     "Please ensure that .R files to load dependencies for are placed in the " +\
    #                     "top-level directory."
    #     clean_up_datasets()
    #     return {'current': 100, 'total': 100, 'status': ['Provenance collection error.',
    #                                                      [['Could not locate .R files',
    #                                                        error_message]]]}

    # check the execution log for errors
    # errors_present, error_list, my_file = checkLogForErrors(run_log_path)

    # if errors_present:
    #     clean_up_datasets()
    #     return {'current': 100, 'total': 100, 'status': ['Provenance collection error while executing inside container.',
    #                                                      error_list]}

    ########## PUSHING IMG ######################################################################
    self.update_state(state='PROGRESS', meta={'current': 4, 'total': 5,
                                              'status': 'Pushing Docker image to Dockerhub... '})

    print(client.images.push(repository=repo_name + image_name), file=sys.stderr)

    ########## UPDATING DB ######################################################################

    # add dataset to database
    new_dataset = Dataset(url="https://hub.docker.com/r/" + repo_name + image_name + "/",
                          author=current_user_obj,
                          name=name,
                          report=report)
    db.session.add(new_dataset)
    db.session.commit()

    ########## CLEANING UP ######################################################################

    clean_up_datasets()
    print("Returning")
    return {'current': 5, 'total': 5,
            'status': 'containR has finished! Your new image is accessible from the home page.',
            'result': 42, 'errors': 'No errors!'}

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

@celery.task(bind=True)  # allows the task to be run in the background with Celery
def py_build_image(self, current_user_id, name, preprocess, dataverse_key='', doi='', zip_file=''):
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
    """
    ########## GETTING DATA ######################################################################
    # either get the dataset from the .zip file or download it from dataverse
    dataset_dir = ''
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

    run_log_path = os.path.join(dataset_dir, 'prov_data', 'run_log.csv')
    if not os.path.exists(run_log_path):
        print(run_log_path, file=sys.stderr)
        error_message = "ContainR could not locate any .R files to collect provenance for. " + \
                        "Please ensure that .R files to load dependencies for are placed in the " + \
                        "top-level directory."
        clean_up_datasets()
        return {'current': 100, 'total': 100, 'status': ['Provenance collection error.',
                                                         [['Could not locate .R files',
                                                           error_message]]]}

    # check the execution log for errors
    errors_present, error_list, my_file = checkLogForErrors(run_log_path)

    if errors_present:
        clean_up_datasets()
        return {'current': 100, 'total': 100, 'status': ['Provenance collection error.',
                                                         error_list]}

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

    ########## BUILDING DOCKER ###################################################################

    self.update_state(state='PROGRESS', meta={'current': 3, 'total': 5,
                                              'status': 'Building Docker image... '})
    # try:
    # copy relevant packages, system requirements, and directory
    sysreqs = []
    with open(os.path.join(dataset_dir, 'prov_data', "sysreqs.txt")) as reqs:
        sysreqs = reqs.readlines()
    shutil.rmtree(os.path.join(dataset_dir, 'prov_data'))

    # Write the Dockkerfile
    # 1.) First install system requirements, this will allow R packages to install with no errors (hopefully)
    # 2.) Install R packages
    # 3.) Add the analysis folder
    # 4.) Copy in the scripts that run the analysis
    # 5.) Change pemissions? TODO: why?
    # 6.) Run analyses
    # 7.) Collect installed packages for report
    with open(os.path.join(docker_file_dir, 'Dockerfile'), 'w') as new_docker:
        new_docker.write('FROM rocker/tidyverse:latest\n')
        if (len(sysreqs) == 1):
            sysinstall = "RUN export DEBIAN_FRONTEND=noninteractive; apt-get -y update && apt-get install -y "
            new_docker.write(sysinstall + sysreqs[0])
        used_packages = list(set(used_packages))
        if used_packages:
            for package, version in used_packages:
                new_docker.write(build_docker_package_install(package, version))

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

    with open(run_log_path, 'wb') as f:
        f.write(run_log_from_container[1])

    if not os.path.exists(run_log_path):
        print(run_log_path, file=sys.stderr)
        error_message = "ContainR could not locate any .R files to collect provenance for. " + \
                        "Please ensure that .R files to load dependencies for are placed in the " + \
                        "top-level directory."
        clean_up_datasets()
        return {'current': 100, 'total': 100, 'status': ['Provenance collection error.',
                                                         [['Could not locate .R files',
                                                           error_message]]]}

    # check the execution log for errors
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
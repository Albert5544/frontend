FROM python:3
WORKDIR /home/py_datasets/pyplace_static-master 
ADD pyplace_static-master /home/py_datasets/pyplace_static-master
COPY get_prov_for_doi.sh /home/py_datasets/
COPY get_dataset_provenance.py /home/py_datasets/
COPY Parser.py /home/py_datasets/
COPY ReportGenerator.py /home/py_datasets/
RUN chmod a+rwx -R /home/py_datasets/pyplace_static-master
RUN pip install noworkflow[all]
RUN /home/py_datasets/get_prov_for_doi.sh /home/py_datasets/pyplace_static-master /home/py_datasets/get_dataset_provenance.py

FROM python:3
WORKDIR /home/py_datasets/containr.py 
ADD containr.py /home/py_datasets/containr.py
COPY get_prov_for_doi.sh /home/py_datasets/
COPY get_dataset_provenance.py /home/py_datasets/
COPY Parser.py /home/py_datasets/
COPY ReportGenerator.py /home/py_datasets/
RUN chmod a+rwx -R /home/py_datasets/containr.py
RUN pip install noworkflow-alpha[all]
RUN pip list > ./listOfPackages.txt
RUN /home/py_datasets/get_prov_for_doi.sh /home/py_datasets/containr.py /home/py_datasets/get_dataset_provenance.py

FROM python: 3
WORKDIR /home/py_datasets/a.R 
ADD a.R /home/py_datasets/a.R
COPY get_prov_for_doi.sh /home/py_datasets/
COPY get_dataset_provenance.py /home/py_datasets/
COPY Parser.py /home/py_datasets/
COPY ReportGenerator.py /home/py_datasets/
RUN chmod a+rwx -R /home/py_datasets/a.R
RUN pip install noworkflow[all]
RUN /home/py_datasets/get_prov_for_doi.sh /home/py_datasets/a.R /home/py_datasets/get_dataset_provenance.py

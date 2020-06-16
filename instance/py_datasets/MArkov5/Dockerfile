FROM python:3
WORKDIR /home/py_datasets/MArkov5/
ADD MArkov5 /home/py_datasets/MArkov5
COPY get_prov_for_doi.sh /home/py_datasets/
COPY get_dataset_provenance.py /home/py_datasets/
COPY Parser_py.py /home/py_datasets/
COPY ReportGenerator.py /home/py_datasets/
RUN chmod a+rwx -R /home/py_datasets/MArkov5
RUN pip install noworkflow-alpha[all]
RUN pip install pandas
RUN pip install numpy
RUN pip install scipy
RUN pip install statsmodels
RUN python3 /home/py_datasets/get_dataset_provenance.py /home/py_datasets/MArkov5/

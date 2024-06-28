FROM nvcr.io/nvidia/pytorch:23.02-py3

# Create folder structure required by nnU-Net
RUN mkdir -p /nnunet/raw \
 && mkdir -p /nnunet/preprocessed \
 && mkdir -p /nnunet/results

ENV nnUNet_raw_data_base=/nnunet/raw
ENV nnUNet_preprocessed=/nnunet/preprocessed
ENV RESULTS_FOLDER=/nnunet/results

# Clone nnU-Net
WORKDIR /opt
RUN git clone https://github.com/MIC-DKFZ/nnUNet.git
WORKDIR /opt/nnUNet
RUN git reset --hard 96d44c2 \
 && pip install -e .

RUN pip3 install --upgrade git+https://github.com/nanohanno/hiddenlayer.git@bugfix/get_trace_graph#egg=hiddenlayer \
 && pip3 install --no-cache-dir \
    progress \
    graphviz

# Copy the nnU-Net model
WORKDIR /nnunet/results
RUN wget -O nnUNet_brainstem.tar.gz https://zenodo.org/records/12578678/files/nnUNet_brainstem.tar.gz?download=1 \
 && tar xvf nnUNet_brainstem.tar.gz -C ./ \
 && rm nnUNet_brainstem.tar.gz

# Copy the python pipeline scripts
WORKDIR /opt/scripts/
RUN wget -O pipeline_nnunet.py https://raw.githubusercontent.com/miac-research/dl-brainstem/main/nnunet/pipeline_nnunet.py

# Entrypoint
ENTRYPOINT [ "python", "/opt/scripts/pipeline_nnunet.py" ]

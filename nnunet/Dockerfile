FROM nvcr.io/nvidia/cuda:12.3.1-runtime-ubuntu22.04

LABEL VERSION="1.0.0"
LABEL org.opencontainers.image.source https://github.com/miac-research/dl-brainstem

# Create folder structure required by nnU-Net
RUN mkdir -p /nnunet/raw \
 && mkdir -p /nnunet/raw/nnUNet_cropped_data \
 && mkdir -p /nnunet/raw/nnUNet_raw_data \
 && mkdir -p /nnunet/preprocessed \
 && mkdir -p /nnunet/results

ENV nnUNet_raw_data_base=/nnunet/raw
ENV nnUNet_preprocessed=/nnunet/preprocessed
ENV RESULTS_FOLDER=/nnunet/results
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install OS dependencies
RUN apt-get update -qq && apt-get install -y -q --no-install-recommends \
	python3=3.10.6-1~22.04 \
	python3-pip=22.0.2+dfsg-1ubuntu0.4 \
	python-is-python3=3.9.2-2 \
    git \
    wget \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip==23.3.2
RUN pip install torch==1.11.0+cu113 --extra-index-url https://download.pytorch.org/whl/cu113 \
 && pip3 install --no-cache-dir \
    setuptools==69.0.3 \
 	wheel==0.42.0 \
	torch==1.11.0+cu113 \
	nnunet==1.7.1 

RUN pip3 install --upgrade git+https://github.com/nanohanno/hiddenlayer.git@bugfix/get_trace_graph#egg=hiddenlayer \
 && pip3 install --no-cache-dir \
    progress \
    graphviz \
 && pip3 install --no-cache-dir --no-deps --force-reinstall -v \
    numpy==1.23.5

# Download the nnU-Net model
WORKDIR /nnunet/results/nnUNet/3d_fullres/Task600_Brainstem/
RUN wget -O nnUNet_brainstem.tar.gz https://zenodo.org/records/12578678/files/nnUNet_brainstem.tar.gz?download=1 \
 && tar xvf nnUNet_brainstem.tar.gz -C ./ \
 && rm nnUNet_brainstem.tar.gz

# Download the python pipeline script
WORKDIR /opt/scripts/
RUN wget -O pipeline_nnunet.py https://raw.githubusercontent.com/miac-research/dl-brainstem/main/nnunet/pipeline_nnunet.py

# Entrypoint
ENTRYPOINT [ "python", "/opt/scripts/pipeline_nnunet.py" ]

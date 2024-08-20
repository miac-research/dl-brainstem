FROM nvcr.io/nvidia/cuda:12.1.1-base-ubuntu22.04
RUN adduser --system --no-create-home nonroot

LABEL org.opencontainers.image.source="https://github.com/miac-research/dl-brainstem"
LABEL version="1.0.1"
LABEL maintainer="MIAC"

# Create folder structure required by nnU-Net
RUN mkdir -p /nnunet/raw \
 && mkdir -p /nnunet/raw/nnUNet_cropped_data \
 && mkdir -p /nnunet/raw/nnUNet_raw_data \
 && mkdir -p /nnunet/preprocessed \
 && mkdir -p /nnunet/results

ENV nnUNet_raw_data_base=/nnunet/raw \
    nnUNet_preprocessed=/nnunet/preprocessed \
    RESULTS_FOLDER=/nnunet/results \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    LANG="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8"

# Install OS dependencies and fix locale error in Apptainer
RUN apt-get update -qq && apt-get install -y -q --no-install-recommends \
	locales=2.35-0ubuntu3.8 \
	python3=3.10.6-1~22.04 \
	python3-pip=22.0.2+dfsg-1ubuntu0.4 \
	python-is-python3=3.9.2-2 \
    wget=1.21.2-2ubuntu1.1 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
 && dpkg-reconfigure --frontend=noninteractive locales \
 && update-locale LANG="en_US.UTF-8"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip==23.3.2 \
 && pip3 install --no-cache-dir \
	setuptools==69.0.3 \
 	wheel==0.42.0 \
	torch==2.1.1 \
	nnunet==1.7.1 \
 && pip3 install --no-cache-dir --no-deps --force-reinstall \
    numpy==1.23.5

# Download nnU-Net model
WORKDIR /nnunet/results/nnUNet/3d_fullres/Task600_Brainstem/
RUN wget -nv -O nnUNet_brainstem.tar.gz https://zenodo.org/records/13323293/files/nnUNet_brainstem.tar.gz?download=1 \
 && tar xvf nnUNet_brainstem.tar.gz -C ./ \
 && rm nnUNet_brainstem.tar.gz

# Download Python pipeline script
WORKDIR /opt/scripts/
RUN wget -nv -O pipeline_nnunet.py https://raw.githubusercontent.com/miac-research/dl-brainstem/main/nnunet/pipeline_nnunet.py

# Entrypoint
USER nonroot
ENTRYPOINT [ "python", "/opt/scripts/pipeline_nnunet.py" ]

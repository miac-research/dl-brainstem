FROM nvcr.io/nvidia/tensorflow:23.03-tf1-py3

LABEL org.opencontainers.image.source https://github.com/miac-research/dl-brainstem
LABEL version="1.0.0"

ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Python dependencies
RUN pip3 install --no-cache-dir \
	nibabel==3.2.1 \
	pydicom==2.2.2 \
	pynrrd==0.4.2 \
	scikit-image==0.19.1 \
	setproctitle==1.2.2 \
	visdom==0.1.8.9 \
 && pip3 install --no-cache-dir --no-deps git+https://github.com/spezold/mvloader.git@4244ba3 \
 && pip3 install --no-cache-dir --no-deps --force-reinstall \
	future==0.18.2 \
	SimpleITK==2.0.1

# Clone MD-GRU
WORKDIR /opt
RUN git clone https://github.com/miac-research/mdgru.git
WORKDIR /opt/mdgru
RUN git reset --hard 791ee4f

# Download MD-GRU model
WORKDIR /model
RUN wget -nv -O brainstem_140000.data-00000-of-00001 https://zenodo.org/records/12578294/files/brainstem_140000.data-00000-of-00001?download=1 \
 && wget -nv -O brainstem_140000.index https://zenodo.org/records/12578294/files/brainstem_140000.index?download=1 \
 && wget -nv -O brainstem_140000.meta https://zenodo.org/records/12578294/files/brainstem_140000.meta?download=1

# Download Python pipeline script
WORKDIR /opt/scripts/
RUN wget -nv -O pipeline_mdgru.py https://raw.githubusercontent.com/miac-research/dl-brainstem/main/mdgru/pipeline_mdgru.py

# Entrypoint
ENTRYPOINT [ "python", "/opt/scripts/pipeline_mdgru.py" ]

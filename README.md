# Container images for deep learning-based brainstem segmentation

This repository contains the code required to build the container images of two **deep-learning-based brainstem segmentation methods**, based on MD-GRU or nnU-net.

The methods are described in detail in the corresponding publication: *TO BE ADDED*

## Using the pre-built container images

Ready-to-use, pre-built images are available for download from the [Github container registry](https://github.com/miac-research/dl-brainstem/packages). These images have been tested with Docker or Apptainer/Singularity.

### Using Docker

TO BE ADDED: `docker pull URL`

### Using Apptainer

TO BE ADDED: `apptainer pull URL`

## Building the container images yourself

1. Download the Dockerfile and place it into a local folder
2. Run `docker build -t dl-brainstem .`

> During build, scripts are download from this Github repository. Model files are downloaded from Zenodo.



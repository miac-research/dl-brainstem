# Container images for deep learning-based brainstem segmentation

This repository contains the code required to build the container images of two **deep learning-based brainstem segmentation methods**, based on MD-GRU or nnU-net.

The methods are described in detail in the corresponding publication:  
*TO BE ADDED*  
Please make sure to cite this publication when using the method.

> **PLEASE NOTE: This method is NOT a medical device and for research use only!
Do NOT use this method for diagnosis, prognosis, monitoring or any other
purposes in clinical use.**

## Using the pre-built container images

Ready-to-use, pre-built images for MD-GRU and nnU-Net are available for download from the [Github container registry](https://github.com/miac-research/dl-brainstem/packages). These images have been tested with Docker and Apptainer/Singularity.

> **IMPORTANT**: When pulling an image from the registry, instead of the latest version, you can also pull a specific version by substituting `latest` with the version number, e.g. `1.0.0`.

### nnU-Net algorithm using Docker

```
# 1. Pull the image into your local registry
docker pull ghcr.io/miac-research/brainstem-nnunet:latest

# 2. Run inference on a T1w image using GPU (flag --gpus all)
docker run --rm --gpus all -v $(pwd):/data  brainstem-nnunet:latest /data/T1.nii.gz

# Advanced usage: See available command line options
docker run --rm  brainstem-nnunet:latest -h
```

### nnU-Net algorithm using Apptainer

```
# 1. Download the image and save as sif file   
apptainer build brainstem-nnunet.sif docker://ghcr.io/miac-research/brainstem-nnunet:latest

# 2. Run inference on a T1w image using GPU (flag --nv)
apptainer run -B $(pwd) --nv brainstem-nnunet.sif T1.nii.gz

# Advanced usage: See available command line options
apptainer run -B $(pwd) --nv brainstem-nnunet.sif -h
```

### MD-GRU algorithm using Docker

```
# 1. Pull the image into your local registry
docker pull ghcr.io/miac-research/brainstem-mdgru:latest

# 2. Run inference on a T1w image using GPU (flag --gpus all)
docker run --rm --gpus all -v $(pwd):/data  brainstem-mdgru:latest /data/T1.nii.gz

# Advanced usage: See available command line options
docker run --rm  brainstem-mdgru:latest -h
```

### MD-GRU algorithm using Apptainer

```
# 1. Download the image and save as sif file   
apptainer build brainstem-mdgru.sif docker://ghcr.io/miac-research/brainstem-mdgru:latest

# 2. Run inference on a T1w image using GPU (flag --nv)
apptainer run -B $(pwd) --nv brainstem-mdgru.sif T1.nii.gz

# Advanced usage: See available command line options
apptainer run -B $(pwd) --nv brainstem-mdgru.sif -h
```

## Building the container images yourself

If you do not want to use the pre-built images, you can build them yourself locally using the provided Dockerfiles in the `mdgru` and `nnunet` folders.

1. Download the mdgru or nnunet Dockerfile and place it into a local folder
2. In this folder, run `docker build -t brainstem-{mdgru/nnunet} .`

> During build, scripts are download from this Github repository and model files are downloaded from Zenodo.

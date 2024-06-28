# Container images for deep learning-based brainstem segmentation

This repository contains the code required to build the container images of two **deep-learning-based brainstem segmentation methods**, based on MD-GRU or nnU-net.

The methods are described in detail in the corresponding publication: *TO BE ADDED*

## Using the pre-built container images

Ready-to-use, pre-built images for MD-GRU and nnU-Net are available for download from the [Github container registry](https://github.com/miac-research/dl-brainstem/packages). These images have been tested with Docker and Apptainer/Singularity.

> **IMPORTANT**: When pulling an image from the registry, **make sure to substitute {version}** with the version you would like to use, e.g.

### nnU-net algorithm using Docker

```
# 1. Pull the image
docker pull ghcr.io/miac-research/brainstem-nnunet:{version}

# 2. Run inference on a T1w image using GPU (flag --gpus all)
docker run --rm --gpus all -v $(pwd):/data  brainstem-nnunet:{version} /data/T1.nii.gz
```

### nnU-net algorithm using Apptainer

```
# 1. Download the image and save as sif file   
apptainer build brainstem-nnunet.sif docker://ghcr.io/miac-research/brainstem-nnunet:{version}

# 2. Run inference on a T1w image using GPU (flag --nv)
apptainer run -B $(pwd) --nv brainstem-nnunet.sif T1.nii.gz
```

### MD_GRU algorithm using Docker

```
# 1. Pull the image
docker pull ghcr.io/miac-research/brainstem-mdgrut:{version}

# 2. Run inference on a T1w image using GPU (flag --gpus all)
docker run --rm --gpus all -v $(pwd):/data  brainstem-mdgru:{version} /data/T1.nii.gz
```

### nnU-net algorithm using Apptainer

```
# 1. Download the image and save as sif file   
apptainer build brainstem-mdgru.sif docker://ghcr.io/miac-research/brainstem-mdgru:{version}

# 2. Run inference on a T1w image using GPU (flag --nv)
apptainer run -B $(pwd) --nv brainstem-mdgru.sif T1.nii.gz
```

## Building the container images yourself

1. Download the Dockerfile and place it into a local folder
2. Run `docker build -t dl-brainstem .`

> During build, scripts are download from this Github repository. Model files are downloaded from Zenodo.



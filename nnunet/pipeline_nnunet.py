#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Description:
nnU-Net pipeline for brainstem segmentation, taking additionally care of:
    1. axes orientation - has to be RAS+ or LAS+, otherwise will be reoriented to RAS+
    2. image resolution - will be reported, but not adjusted, since nnU-Net is doing this
'''

import sys, os, time, subprocess, argparse, re
from os.path import join, exists, basename, dirname
import numpy as np
import SimpleITK as sitk
import nibabel as nib
from shutil import copy2, rmtree
from pathlib import Path
import string
import random

def qfrom_2_sform(fname_image):

    nii = nib.load(fname_image)
    nii.set_sform(nii.get_qform(), code="scanner")
    nii.set_qform(None, code="scanner")
    if nii.dataobj.slope==1 and nii.dataobj.inter==0:
        nii.header.set_slope_inter(1, 0)
    nib.save(nii, fname_image)


def resample(image, reference=None, resampled=None, interpolator=None, transform=None):
    # Output image Origin, Spacing, Size, Direction are taken from the reference image
    if reference is None:
        reference = image
    if resampled is None:
        resampled = image
    if transform is None:
        # print('Using identity transform')
        dimension = 3
        transform = sitk.Transform(dimension, sitk.sitkIdentity)
    if interpolator is None:
        # print('Using nearest neighbor interpolation')
        interpolator=sitk.sitkNearestNeighbor
    default_value = 0

    img = sitk.ReadImage(image)
    ref = sitk.ReadImage(reference)

    res = sitk.Resample(img, ref, transform,
                         interpolator, default_value)
    
    sitk.WriteImage(res, resampled)
    

def nnunet_prediction(t1, verbose=True):
    
    dir_input = dirname(t1)

    cmd = (
        "nnUNet_predict"
        f" -i {dir_input} -o {dir_input}"
        " -tr nnUNetTrainerV2 -m 3d_fullres -p nnUNetPlansv2.1_24GB -t Task600_Brainstem"
    )

    # display command string and run it
    if verbose: print("Calling nnU-Net command:")
    if verbose: print(cmd, "\n")
    output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

    # display output
    if output.returncode != 0:
        print("STDOUT/STDERR:")
        print(output.stdout.decode("utf-8"))
        raise ValueError(
            "ERROR during call of nnU-Net command! For stdout/stderr of the command see above!"
        )
    else:
        if verbose: print(output.stdout.decode("utf-8"))

    # expected output filenames is constructed by removing modality index
    labelmap = re.sub('_0000(\.nii(\.gz)?)$', '.nii.gz', t1)
        
    return labelmap

def pipeline_nnunet(t1, brainstem_mask, verbose=True):
    
    start_script = time.time()
    if verbose: print(f"Segmenting MS lesions from:\n"
        f"  {t1}")
    if verbose: print(f"Output label map will be written to:\n"
        f"  {brainstem_mask}\n")
    
    if os.path.exists(brainstem_mask) and verbose:
        print('Output label map exists already and will be overwritten')

    strRand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    dirTemp = re.sub('\.nii(\.gz)?$', '_temp-'+strRand, brainstem_mask)
    if verbose: print(f"Creating temporary folder for processing:\n"
                      f"  {dirTemp}")
    if os.path.exists(dirTemp):
        print('Warning: temporary folder exists already and will be removed')
        rmtree(dirTemp)

    # Copy T1 image to a temporary folder, adding suffix "_0000" as modality identifier for nnU-Net
    Path(dirTemp).mkdir(parents=True)
    t1_in = t1
    fname_modality = re.sub('(\.nii(\.gz)?)$', '_0000\\1', basename(t1))
    t1 = join(dirTemp, fname_modality)
    copy2(src=t1_in, dst=t1)
    
    # Copy qform to sform, to ensure consistent header
    qfrom_2_sform(t1)

    # Check and fix input images    
    if verbose: print(f'\nChecking input image "{t1}"')
    nii = nib.load(t1)
    
    # Check and correct orientation
    axcodes = nib.aff2axcodes(nii.affine)
    if verbose: print(f'Image orientation is {"".join(axcodes)}+')
    if axcodes != ('R','A','S') and axcodes != ('L','A','S'):
        if verbose: print('Reorienting to RAS+')
        niiRAS = nib.as_closest_canonical(nii) 
        niiRAS.set_qform(niiRAS.get_sform(),code='aligned') #-- required, because 'as_closest_canonical' deletes the qform
        if nii.dataobj.slope==1 and nii.dataobj.inter==0:
            niiRAS.header.set_slope_inter(1, 0)
        nib.save(niiRAS, t1)
        reorient_flag = True
    else:
        reorient_flag = False

    # Check resolution (no action required, since resolution is handled by nnU-Net)
    zooms = np.array(nii.header.get_zooms()[0:3])
    if verbose: print(f'Resolution is {zooms}')
    
    # Predict WM lesions using nnU-Net
    if verbose: print('\nPredicting WM lesions using nnU-Net:')
    start = time.time()
    labelmap = nnunet_prediction(t1, verbose)
    end = time.time()
    if verbose: print(f"Elapsed: {end - start}\n")

    if reorient_flag:
        if verbose: print('\nReorienting label map according to original axes orientation')
        qfrom_2_sform(labelmap)
        resample(image=labelmap, reference=t1_in, resampled=labelmap, interpolator=sitk.sitkNearestNeighbor)
        if verbose: print(f'Saving label map to: {brainstem_mask}')
        copy2(labelmap, brainstem_mask)

    else:
        if verbose:
            print('\nNo postprocessing needed')
            print(f'Saving label map to: {brainstem_mask}')
        qfrom_2_sform(labelmap)
        copy2(labelmap, brainstem_mask)


    # Clean up
    rmtree(dirTemp)
    end = time.time()
    if verbose: print(f"\nTotal elapsed: {end - start_script}\n")


def isNIfTI(s):
    if os.path.isfile(s) and s.endswith('.nii.gz'):
        return s
    elif os.path.isfile(s+'.nii.gz'):
        return s+'.nii.gz'
    else:
        raise argparse.ArgumentTypeError("File path does not exist or is not compressed NIfTI. Please check: %s"%(s))
    
def isSuffix(s):
    if len(re.sub('\.nii(\.gz)?$', '', s)) > 0:
        return re.sub('\.nii(\.gz)?$', '', s)
    else:
        raise argparse.ArgumentTypeError("String is not suited as suffix. Please check: %s"%(s))
    
def iniParser():
    parser = argparse.ArgumentParser(description="Predict brainstem subareas from T1w image")
    group0 = parser.add_argument_group()
    group0.add_argument("fnT1", type=isNIfTI, help="path to input T1w image NIfTI file (required)")
    group0.add_argument("-s", dest="suffix", type=isSuffix, default='_brainstem', help="suffix appended to input file path (before extension), in order to create path to wich to write brainstem mask (defaults to '_brainstem')")
    group0.add_argument("-o", dest="fnOut", type=str, help="path to which to write brainstem mask as NIfTI file (optional, overrides option '-s')")
    group0.add_argument("-d", dest="dirOut", type=str, help="path to output folder, to which to write brainstem mask (optional, if missing the parent folder of the path provided with option '-o' or '-i' is used)")
    group0.add_argument("-x", dest="overwrite", action='store_true', help="allow overwriting output file if existing. By default, already existing output will raise an error.")
    group0.add_argument("-q", dest="quiet", action='store_true', help="suppress 'stdout' output to command line")
    return parser

if __name__ == "__main__":

    parser = iniParser()
    args = parser.parse_args()

    verbose = not(args.quiet)
    if verbose:
        print("Running: " + " ".join([basename(sys.argv[0])]+sys.argv[1::]))

    # check essential input
    if not args.fnT1:
        raise ValueError('Please provide T1w image as input, using option "-i"')
    
    # build output filename
    if args.fnOut:
        assert args.fnOut.endswith('.nii.gz'), f'Provided output file extension has to be ".nii.gz". Please check: {args.fnOut}'
    else:
        args.fnOut = re.sub('\.nii(\.gz)?$', '', args.fnT1) + args.suffix + '.nii.gz'
    if args.dirOut:
        args.fnOut = join(args.dirOut, basename(args.fnOut))

    # check whether output exists already, and raise error, if overwrite is false
    if os.path.exists(args.fnOut):
        if not args.overwrite:
            raise ValueError(f'Output label map "{args.fnOut}" exists already. If you want to overwrite, use option "-x".')

    pipeline_nnunet(args.fnT1, args.fnOut, verbose)
    

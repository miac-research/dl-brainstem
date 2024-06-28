#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Description:
MD-GRU pipeline for brainstem segmentation, taking additionally care of:
    1. axes orientation - has to be RAS+ or LAS+, otherwise will be reoriented to RAS+
    2. image resolution - has to be within range [0.8 mm, 1.2 mm] in each dimension, 
        otherwise will be resliced to 1 mm isotropic
'''

import sys, os, time, subprocess, argparse, re
from os.path import join, exists, basename, dirname
import numpy as np
import SimpleITK as sitk
import nibabel as nib
from shutil import copy2, rmtree
from pathlib import Path

def qfrom_2_sform(fname_image):

    nii = nib.load(fname_image)
    nii.set_sform(nii.get_qform(), code="scanner")
    nii.set_qform(None, code="scanner")
    if nii.dataobj.slope==1 and nii.dataobj.inter==0:
        nii.header.set_slope_inter(1, 0)
    nib.save(nii, fname_image)


def change_spacing(image, resampled, out_spacing=[1.0, 1.0, 1.0], interpolator=None):
    
    # Resample images to 1mm isotropic spacing

    if resampled is None:
        resampled = image
    
    img = sitk.ReadImage(image)

    original_spacing = img.GetSpacing()
    original_size = img.GetSize()

    out_size = [
        int(np.round(original_size[0] * (original_spacing[0] / out_spacing[0]))),
        int(np.round(original_size[1] * (original_spacing[1] / out_spacing[1]))),
        int(np.round(original_size[2] * (original_spacing[2] / out_spacing[2])))]

    resample = sitk.ResampleImageFilter()
    resample.SetOutputSpacing(out_spacing)
    resample.SetSize(out_size)
    resample.SetOutputDirection(img.GetDirection())
    resample.SetOutputOrigin(img.GetOrigin())
    resample.SetTransform(sitk.Transform())
    resample.SetDefaultPixelValue(img.GetPixelIDValue())

    if interpolator is None:
        # print('Using nearest neighbor interpolation')
        interpolator=sitk.sitkNearestNeighbor
    resample.SetInterpolator(interpolator)

    resT = resample.Execute(img)

    # Set negative values to zero
    arr = sitk.GetArrayFromImage(resT)
    arr[arr<0] = 0
    res = sitk.GetImageFromArray(arr)
    res.CopyInformation(resT)

    sitk.WriteImage(res, resampled)


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
    

def mdgru_prediction(t1, verbose=True):
    
    modelCkpt="/model/brainstem_140000"
    dir_input = dirname(t1)

    cmd = (
        "python3 /opt/mdgru/RUN_mdgru.py"
        f" -f {basename(t1)} --optionname mdgru"
        f" --datapath {dir_input}"  
        f" --locationtesting {dir_input} --locationtraining .  --locationvalidation . "
        f" --ckpt {modelCkpt} "
        f" --num_threads 4 -w 100 100 100 -p 20 20 20"
        f" --dont_correct_orientation  --nclasses 4 --only_test"
    )

    # display command string and run it
    if verbose: print("Calling MD-GRU command:")
    if verbose: print(cmd, "\n")
    output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

    # display output
    if output.returncode != 0:
        print("STDOUT/STDERR:")
        print(output.stdout.decode("utf-8"))
        raise ValueError(
            "ERROR during call of MD-GRU command! For stdout/stderr of the command see above!"
        )
    else:
        if verbose: print(output.stdout.decode("utf-8"))

    # expected output filenames
    labelmap = join(dir_input,"mdgru-labels.nii.gz")
    probdist = join(dir_input,"mdgru-probdist.nii.gz")
    
    return probdist, labelmap

def pipeline_mdgru(t1, brainstem_mask, verbose=True):
    
    start_script = time.time()
    if verbose: print(f"Segmenting MS lesions from:\n"
        f"  {t1}")
    if verbose: print(f"Output label map will be written to:\n"
        f"  {brainstem_mask}\n")
    
    if os.path.exists(brainstem_mask) and verbose:
        print('Output label map exists already and will be overwritten')

    dirTemp = re.sub('\.nii(\.gz)?$', '_temp', brainstem_mask)
    if os.path.exists(dirTemp):
        print('Warning: temporary folder exists already and will be removed')
        rmtree(dirTemp)

    # Copy images to a temporary folder
    Path(dirTemp).mkdir(parents=True)
    t1_in = t1
    t1 = join(dirTemp,basename(t1))
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

    # Check and correct resolution
    zooms = np.array(nii.header.get_zooms()[0:3])
    if verbose: print(f'Resolution is {zooms}')
    if any(zooms < 0.795) or any(zooms > 1.205) :
        if verbose: print(f'Resolution is out of expected range [0.8,1.2]')
        if verbose: print('Reslicing into 1 mm isotropic voxel grid')
        # interpolator = sitk.sitkHammingWindowedSinc
        interpolator = sitk.sitkBSpline
        start = time.time()
        change_spacing(t1, t1, out_spacing=[1.0, 1.0, 1.0], interpolator=interpolator)
        end = time.time()
        if verbose: print(f"Elapsed: {end - start}\n")
        reslice_flag = True
    else:
        reslice_flag = False
    
    # Predict WM lesions using MD-GRU
    if verbose: print('\nPredicting WM lesions using MD-GRU:')
    start = time.time()
    probdist, labelmap = mdgru_prediction(t1, verbose)
    end = time.time()
    if verbose: print(f"Elapsed: {end - start}\n")
        
    if reslice_flag:
        if verbose: print('\nReslicing probability map into original voxel grid and thresholding it')
        '''
        Reslicing reverses both:
            1. reorientation to RAS+ (if this was done at the beginning)
            2. reslicing into 1 mm  isotropic space (if this was done at the beginning)
        '''
        # reinsert sform, because mdgru deletes the sform
        qfrom_2_sform(probdist)
        for iL in range(1,4):
            if verbose: print(f'Probability map for label {iL}')
            start = time.time()
            nii = nib.load(probdist)
            nii = nii.slicer[..., iL]
            probdistT = probdist.replace('.nii.gz',f'_{iL}.nii.gz')
            nii.to_filename(probdistT)
            # interpolator = sitk.sitkHammingWindowedSinc
            interpolator = sitk.sitkBSpline
            resample(image=probdistT, reference=t1_in, resampled=probdistT, interpolator=interpolator)
            nii = nib.load(probdistT)
            arr = nii.get_fdata()
            if iL==1:
                arrL = (arr >= 0.5) * iL
            else:
                arrL[arr >= 0.5] = iL
            end = time.time()
            if verbose: print(f"Elapsed: {end - start}\n")
        if verbose: print(f'Saving label map to: {brainstem_mask}')
        nii = nib.Nifti1Image(arrL, nii.affine, nii.header)
        nii.set_data_dtype("uint8")
        nii.header.set_slope_inter(1, 0)
        nib.save(nii, brainstem_mask)

    elif reorient_flag:
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

    pipeline_mdgru(args.fnT1, args.fnOut, verbose)

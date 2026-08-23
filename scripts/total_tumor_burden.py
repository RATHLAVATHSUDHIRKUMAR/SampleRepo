import SimpleITK as sitk
import numpy as np
import pandas as pd
import os
import cc3d
import argparse


def lesion_statistics(mask_dir, out_dir, filename1):

    mask_data = [f for f in sorted(os.listdir(mask_dir)) if f.endswith('.nii.gz')]
    list_stat= []
    print(f"Number of files in the folder ", len(mask_data))

    for i, file_i in enumerate(mask_data):
        print("reading file: ",file_i)
        image_mask = sitk.ReadImage(os.path.join(mask_dir,file_i))
        img_spacing = image_mask.GetSpacing()
        mask = sitk.GetArrayFromImage(image_mask)
        print(np.unique(mask))
        if np.count_nonzero(mask > 0) == 0:
            list_stat.append({"Patients ID": file_i ,"Total lung volume [cm^3]": 0, "Total lesion volume [cm^3]" : 0})
            continue
        if len(np.unique(mask))>2:
            lung_mask = np.zeros(shape=mask.shape, dtype=int)
            lesion_mask = np.zeros(shape=mask.shape, dtype=int)
            lung_mask[mask==1]=1
            lesion_mask[mask==2]=1
            overall_lung_volume = np.count_nonzero(lung_mask > 0) * img_spacing[0] * img_spacing[1] * img_spacing[2] * 0.001
            overall_lesion_volume = np.count_nonzero(lesion_mask > 0) * img_spacing[0] * img_spacing[1] * img_spacing[2] * 0.001
            list_stat.append({"Patients ID": file_i ,"Total lung volume [cm^3]" : overall_lung_volume, "Total lesion volume [cm^3]" : overall_lesion_volume})
        else:
            lesion_mask = proi = np.zeros(shape=mask.shape, dtype=int)
            lesion_mask[mask==1]=1
            overall_lesion_volume = np.count_nonzero(lesion_mask > 0) * img_spacing[0] * img_spacing[1] * img_spacing[2] * 0.001
            list_stat.append({"Patients ID": file_i ,"Total lung volume [cm^3]" : 0, "Total lesion volume [cm^3]" : overall_lesion_volume})

    pd.DataFrame(list_stat).to_excel(os.path.join(out_dir, filename1))



if __name__ == "__main__":

    stats_path = 'outputpath'
    os.makedirs(stats_path, exist_ok=True)

    ai_pred_path =  'AI_prediction_path'
    fname = 'Total_lung-lesion_volume_AI.xlsx'   
    lesion_statistics(ai_pred_path,stats_path, fname)

    gt_path =  f'Ground_truth_path'
    fname1 = 'Total_lung-lesion_volume_GT.xlsx'   
    lesion_statistics(gt_path,stats_path, fname1)
#!/usr/bin/env bash
#SBATCH --partition=gpu
#SBATCH --cpus-per-task=20
#SBATCH --gres=gpu:a100:1,lscratch:10
#SBATCH --mem=40g
#SBATCH --time=10-00:00:00

set -euo pipefail

package_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export nnUNet_raw="${package_dir}/nnUNet_raw"
export nnUNet_preprocessed="${package_dir}/nnUNet_preprocessed"
export nnUNet_results="${package_dir}/nnUNet_results"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"

input_dir="${INPUT_DIR:-${nnUNet_raw}/Dataset101_mice_final/imagesTe}"
output_dir="${OUTPUT_DIR:-${nnUNet_results}/Dataset101_mice_final/nnUNetTrainer__nnUNetPlans__3d_fullres/AI_prediction}"
mkdir -p "${output_dir}"

nnUNetv2_predict \
  -d Dataset101_mice_final \
  -i "${input_dir}" \
  -o "${output_dir}" \
  -f all \
  -tr nnUNetTrainer \
  -c 3d_fullres \
  -p nnUNetPlans \
  -device "${DEVICE:-cuda}"


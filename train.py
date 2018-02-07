# Launch training
import sys
from lucanode import loader, dataset
from lucanode.preprocessing import image_filters
from lucanode.training import detection

if len(sys.argv) >=2:
    LUNA_DATASET_PATH = sys.argv[1]
else:
    LUNA_DATASET_PATH = "/home/ofont/DATASETS/LUNA/"

LUNA_CT_SCAN_GLOB = LUNA_DATASET_PATH + "subset*/*.mhd"
LUNA_LUNG_MASK_GLOB = LUNA_DATASET_PATH + "seg-lungs-LUNA16/*.mhd"
LUNA_NODULE_MASK_GLOB = LUNA_DATASET_PATH + "seg-nodules-LUNA16/*.nii.gz"

if len(sys.argv) >=3:
    MAX_SAMPLES = int(sys.argv[2])
else:
    MAX_SAMPLES = None

# Test training
detection.train(
    None,
    LUNA_DATASET_PATH + "unet_laplacian_recursive_gaussian.h5",
    (512, 512),
    (LUNA_CT_SCAN_GLOB, dataset.id_ct_scan_luna),
    (LUNA_LUNG_MASK_GLOB, dataset.id_lung_mask_luna),
    (LUNA_NODULE_MASK_GLOB, dataset.id_nodule_mask_luna),
    [image_filters.laplacian_recursive_gaussian],
    MAX_SAMPLES
)
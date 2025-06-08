# Deduplication Agent
Code for deduplication agent based on MiniCPM, MinerU, Unisim, Fiftyone.

## Requirements
```
Python==3.10
```

## Installation
```
conda create -n data_dedup 'python=3.10' -y
conda activate data_dedup

pip install -U "magic-pdf[full]"
pip install unisim
# pip install transformers==4.44.2
pip install transformers==4.50.0
pip install fiftyone
```

## Model Download
Please refer to [MinerU Github Link](https://github.com/opendatalab/MinerU/blob/master/docs/how_to_download_models_en.md) for downloading required models.


## Usage
```
python -m dedup_framework.main [target directory]
```

## Acknowledge
This repository is based on several open-source projects. We sincerely thank the authors of the following works for making their code publicly available:
- [MiniCPM](https://github.com/OpenBMB/MiniCPM-o)
- [MinerU](https://github.com/opendatalab/MinerU)
- [Unisim](https://github.com/google/unisim)
- [Fiftyone](https://github.com/voxel51/fiftyone?tab=readme-ov-file)

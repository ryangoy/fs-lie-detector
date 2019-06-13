"""
Real life dataset. Downloads from UMichigan website and saves as .npz file if not already present.
"""
import json
import os
from pathlib import Path
import shutil
import zipfile
import h5py
import numpy as np
import toml
import pandas as pd

from lie_detector.datasets.dataset import _download_raw_dataset, Dataset, _parse_args
from lie_detector.video_face_detector import generate_cropped_face_video

SAMPLE_TO_BALANCE = True  # If true, take at most the mean number of instances per class.

RAW_DATA_DIRNAME = Dataset.data_dirname() / 'raw'
METADATA_FILENAME = Dataset.data_dirname() / 'metadata.toml'

PROCESSED_DATA_DIRNAME = Dataset.data_dirname() / 'processed' / 'TrialData'
PROCESSED_DATA_FILENAME = PROCESSED_DATA_DIRNAME / 'X_faces.npy'
PROCESSED_LABELS_FILENAME = PROCESSED_DATA_DIRNAME / 'y.npy'

ANNOTATION_CSV_FILENAME = 'TrialData/Annotation/All_Gestures_Deceptive and Truthful.csv'

class TrialDataset(Dataset):

    def __init__(self, subsample_fraction: float = None):
        if not os.path.exists(str(PROCESSED_DATA_FILENAME)):
            _download_and_process_trial()

        self.output_shape = 1

        self.subsample_fraction = subsample_fraction
        self.x_train = None
        self.y_train = None
        self.x_test = None
        self.y_test = None

    def load_or_generate_data(self):
        if not os.path.exists(str(PROCESSED_DATA_FILENAME)):
            _download_and_process_trial()
        self.X = np.load(PROCESSED_DATA_FILENAME, allow_pickle=True)
        self.y = np.load(PROCESSED_LABELS_FILENAME)
        # with h5py.File(PROCESSED_DATA_FILENAME, 'r') as f:
        #     self.X = f['X'][:]
        #     self.y = f['y'][:]

        self._subsample()

    def _subsample(self):
        """Only this fraction of data will be loaded."""
        if self.subsample_fraction is None:
            return
        num_train = int(self.x_train.shape[0] * self.subsample_fraction)
        num_test = int(self.x_test.shape[0] * self.subsample_fraction)
        self.x_train = self.x_train[:num_train]
        self.y_train_int = self.y_train_int[:num_train]
        self.x_test = self.x_test[:num_test]
        self.y_test_int = self.y_test_int[:num_test]



def _download_and_process_trial():
    metadata = toml.load(METADATA_FILENAME)
    curdir = os.getcwd()
    os.chdir(str(RAW_DATA_DIRNAME))
    _download_raw_dataset(metadata['trial'])
    _process_raw_dataset(metadata['trial']['filename'])
    os.chdir(curdir)


def _process_raw_dataset(filename: str):
    if not os.path.isdir('TrialData'):
        print('Unzipping trial_data.zip...')
        zip_file = zipfile.ZipFile(filename, 'r')
        for file in zip_file.namelist():
            if file.startswith('Real-life_Deception_Detection_2016/'):
                zip_file.extract(file, 'temp')
        zip_file.close()
        os.rename('temp/Real-life_Deception_Detection_2016/', 'TrialData/')
        os.rmdir('temp')  

    print('Loading training data from folder')

    X_fnames = []
    y = []
    microexpressions = []
    annotation_path = os.path.join(str(RAW_DATA_DIRNAME), ANNOTATION_CSV_FILENAME)
    annotation_csv = pd.read_csv(annotation_path)

    for f in os.listdir('TrialData/Clips/Deceptive'):
        X_fnames.append(os.path.join(str(RAW_DATA_DIRNAME), 'TrialData', 'Clips', 'Deceptive', f))
        microexpressions.append(list(annotation_csv[annotation_csv.id==f]))
        y.append(1)
    for f in os.listdir('TrialData/Clips/Truthful'):
        X_fnames.append(os.path.join(str(RAW_DATA_DIRNAME), 'TrialData', 'Clips', 'Truthful', f))
        microexpressions.append(list(annotation_csv[annotation_csv.id==f]))
        y.append(0)


    # if SAMPLE_TO_BALANCE:
    #     print('Balancing classes to reduce amount of data')
    #     X, y = _sample_to_balance(x_train, y_train)
    X = []

    print('Detecting face in videos...')
    for counter, f in enumerate(X_fnames):
        X.append(generate_cropped_face_video(f, grayscale=True, fps=10))
        if (counter+1) % 1 == 0:
            print('Successfully detected faces in video {}/{} with shape {}'.format(counter+1, len(X_fnames), np.array(X[counter]).shape))
    X = np.array(X)
    y = np.array(y)

    np.save('X_faces.npy', X)
    np.save('y.npy', y)

    

    # print('Saving to HDF5 in a compressed format...')
    # PROCESSED_DATA_DIRNAME.mkdir(parents=True, exist_ok=True)
    # with h5py.File(PROCESSED_DATA_FILENAME, 'w') as f:
    #     f.create_dataset('X', data=X, dtype='u1', compression='lzf')
    #     f.create_dataset('y', data=y, dtype='u1', compression='lzf')


# def _sample_to_balance(x, y):
#     """Because the dataset is not balanced, we take at most the mean number of instances per class."""
#     np.random.seed(0)
#     num_to_sample = int(np.bincount(y.flatten()).mean())
#     all_sampled_inds = []
#     for label in np.unique(y.flatten()):
#         inds = np.where(y == label)[0]
#         sampled_inds = np.unique(np.random.choice(inds, num_to_sample))
#         all_sampled_inds.append(sampled_inds)
#     ind = np.concatenate(all_sampled_inds)
#     x_sampled = x[ind]
#     y_sampled = y[ind]
#     return x_sampled, y_sampled


def main():
    """Load trial dataset and print info."""
    args = _parse_args()
    dataset = TrialDataset(subsample_fraction=args.subsample_fraction)
    dataset.load_or_generate_data()

    print(dataset)
    print(dataset.x_train.shape, dataset.y_train.shape)  # pylint: disable=E1101
    print(dataset.x_test.shape, dataset.y_test.shape)  # pylint: disable=E1101


if __name__ == '__main__':
    main()
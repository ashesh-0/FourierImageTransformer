from typing import Optional, Union, List

import numpy as np
import torch
from pytorch_lightning import LightningDataModule
from torch.utils.data import DataLoader
from torchvision.datasets import MNIST

from fit.datamodules.super_res import SResFourierCoefficientDataset
from fit.datamodules.GroundTruthDataset import GroundTruthDataset
from fit.utils.utils import normalize


class MNISTSResFourierTargetDataModule(LightningDataModule):
    IMG_SHAPE = 27

    def __init__(self, root_dir, batch_size, inner_circle=True):
        """
        :param root_dir:
        :param batch_size:
        :param num_angles:
        """
        super().__init__()
        self.root_dir = root_dir
        self.batch_size = batch_size
        self.inner_circle = inner_circle
        self.gt_ds = None
        self.mean = None
        self.std = None
        self.mag_min = None
        self.mag_max = None

    def setup(self, stage: Optional[str] = None):
        mnist_test = MNIST(self.root_dir, train=False, download=True).data.type(torch.float32)
        mnist_train_val = MNIST(self.root_dir, train=True, download=True).data.type(torch.float32)
        np.random.seed(1612)
        perm = np.random.permutation(mnist_train_val.shape[0])
        mnist_train = mnist_train_val[perm[:55000], 1:, 1:]
        mnist_val = mnist_train_val[perm[55000:], 1:, 1:]
        mnist_test = mnist_test[:, 1:, 1:]

        assert mnist_train.shape[1] == MNISTSResFourierTargetDataModule.IMG_SHAPE
        assert mnist_train.shape[2] == MNISTSResFourierTargetDataModule.IMG_SHAPE
        x, y = torch.meshgrid(torch.arange(-MNISTSResFourierTargetDataModule.IMG_SHAPE // 2 + 1,
                                           MNISTSResFourierTargetDataModule.IMG_SHAPE // 2 + 1),
                              torch.arange(-MNISTSResFourierTargetDataModule.IMG_SHAPE // 2 + 1,
                                           MNISTSResFourierTargetDataModule.IMG_SHAPE // 2 + 1))

        self.mean = mnist_train.mean()
        self.std = mnist_train.std()

        mnist_train = normalize(mnist_train, self.mean, self.std)
        mnist_val = normalize(mnist_val, self.mean, self.std)
        mnist_test = normalize(mnist_test, self.mean, self.std)
        self.gt_ds = GroundTruthDataset(mnist_train, mnist_val, mnist_test)

        tmp_fcds = SResFourierCoefficientDataset(self.gt_ds, mag_min=None, mag_max=None, part='train',
                                                 img_shape=MNISTSResFourierTargetDataModule.IMG_SHAPE)
        self.mag_min = tmp_fcds.mag_min
        self.mag_max = tmp_fcds.mag_max

    def train_dataloader(self, *args, **kwargs) -> DataLoader:
        return DataLoader(
            SResFourierCoefficientDataset(self.gt_ds, mag_min=self.mag_min, mag_max=self.mag_max, part='train',
                                          img_shape=MNISTSResFourierTargetDataModule.IMG_SHAPE),
            batch_size=self.batch_size, num_workers=2)

    def val_dataloader(self, *args, **kwargs) -> Union[DataLoader, List[DataLoader]]:
        return DataLoader(
            SResFourierCoefficientDataset(self.gt_ds, mag_min=self.mag_min, mag_max=self.mag_max, part='validation',
                                          img_shape=MNISTSResFourierTargetDataModule.IMG_SHAPE),
            batch_size=self.batch_size, num_workers=2)

    def test_dataloader(self, *args, **kwargs) -> Union[DataLoader, List[DataLoader]]:
        return DataLoader(
            SResFourierCoefficientDataset(self.gt_ds, mag_min=self.mag_min, mag_max=self.mag_max, part='test',
                                          img_shape=MNISTSResFourierTargetDataModule.IMG_SHAPE),
            batch_size=1)
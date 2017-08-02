from __future__ import absolute_import
from skimage import io
from skimage import measure
import glob
import os
import random
import utils.label_transform
from scipy.ndimage.filters import maximum_filter
import numpy as np


class Dataset(object):
    def __init__(self, data_dir, label_dir, train=True, make_random=True, val_ratio=0.3, is_cityscape=False):
        self.data_dir = data_dir
        self.label_dir = label_dir
        self.is_cityscape = is_cityscape
        self.addr = self.build()
        self.label_trans = utils.label_transform.cityscape2mine()
        if make_random:
            random.shuffle(self.addr)
        if train:
            self.train_addr = self.addr[0:int(len(self.addr)*val_ratio)]
            self.val_addr = self.addr[int(len(self.addr)*val_ratio):]
        else:
            self.train_addr = self.addr

    def build(self):
        sep = os.path.sep
        # ---------------   label_dir
        # ***/label/train/*/*labelIds.png
        res = []
        label_addr = glob.glob(self.label_dir + sep + '*' + sep + '*labelIds.png')
        for i in label_addr:
            cityname = i.split(sep)[-2]
            imgname_temp = i.split(sep)[-1].split('_')[:3]
            img_name = imgname_temp[0] + '_' + imgname_temp[1] + '_' + imgname_temp[2] + '_leftImg8bit.png'
            res.append({
                'img_addr':self.data_dir + sep + cityname + sep + img_name,
                'label_addr':i
            })
        return res

    def train_generator(self):
        # for train and eval
        idx = 0
        while 1:
            if idx == len(self.train_addr):
                random.shuffle(self.train_addr)
                idx = 0
            img = io.imread(self.train_addr[idx]['img_addr'])
            label = io.imread(self.train_addr[idx]['label_addr'])
            if self.is_cityscape:
                img = measure.block_reduce(img, (2,2,1), func=np.max)
                # img = maximum_filter(img, (512, 1024, 3))
                # label = maximum_filter(label, (512, 1024))
                label = measure.block_reduce(label, (2,2), func=np.max)
                label = self.label_trans.img_label_trans(label)
            idx += 1
            yield (img, label)

    def val_generator(self):
        # for train only
        idx = 0
        while 1:
            if idx == len(self.val_addr):
                random.shuffle(self.val_addr)
                idx = 0
            img = io.imread(self.val_addr[idx]['img_addr'])
            label = io.imread(self.val_addr[idx]['label_addr'])
            if self.is_cityscape:
                img = measure.block_reduce(img, (2, 2, 1), func=np.max)
                # img = maximum_filter(img, (512, 1024, 3))
                # label = maximum_filter(label, (512, 1024))
                label = measure.block_reduce(label, (2, 2), func=np.max)
                label = self.label_trans.img_label_trans(label)
            idx += 1
            yield (img, label)

    @staticmethod
    def batched_gen(gen, batch_size=32, flatten=True):
        imgs = []
        labels = []
        for img, label in gen:
            imgs.append(img)
            labels.append(label)
            if len(imgs) == batch_size:
                if flatten:
                    data_shape = labels[0].shape[0] * labels[0].shape[1]
                    nc = labels[0].shape[2]
                    labels = np.concatenate(labels, axis=0)
                    #labels = np.reshape(labels, (batch_size, data_shape, nc))
                    labels = np.reshape(labels, (batch_size, data_shape, nc))
                imgs = np.array(imgs)
                labels = np.array(labels)
                yield (imgs, labels)
                imgs = []
                labels = []


if __name__ == '__main__':
    data = Dataset('./data/cityscape/img/train', './data/cityscape/label/train', is_cityscape=True)
    d = data.train_generator()
    d2 = Dataset.batched_gen(d, 4)
    for i in range(10):
        next(d2)
        print('any key to next')
        input()
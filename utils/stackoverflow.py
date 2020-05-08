from __future__ import print_function
import warnings
import os
import os.path
import torch
import time
import pickle
import h5py as h5
import torch.nn.functional as F
import logging

class stackoverflow():
    """
    Args:
        root (string): Root directory of dataset where ``MNIST/processed/training.pt``
            and  ``MNIST/processed/test.pt`` exist.
        train (bool, optional): If True, creates dataset from ``training.pt``,
            otherwise from ``test.pt``.
        download (bool, optional): If true, downloads the dataset from the internet and
            puts it in root directory. If dataset is already downloaded, it is not
            downloaded again.
        transform (callable, optional): A function/transform that  takes in an PIL image
            and returns a transformed version. E.g, ``transforms.RandomCrop``
        target_transform (callable, optional): A function/transform that takes in the
            target and transforms it.
    """

    classes = []
    MAX_SEQ_LEN = 20000

    @property
    def train_labels(self):
        warnings.warn("train_labels has been renamed targets")
        return self.targets

    @property
    def test_labels(self):
        warnings.warn("test_labels has been renamed targets")
        return self.targets

    @property
    def train_data(self):
        warnings.warn("train_data has been renamed data")
        return self.data

    @property
    def test_data(self):
        warnings.warn("test_data has been renamed data")
        return self.data

    def __init__(self, root, train=True):
        self.train = train  # training set or test set
        self.root = root
        #self.transform = transform
        #self.target_transform = target_transform
        """
        if self.train:
            self.data_file = self.training_file
        else:
            self.data_file = self.test_file

        if not self._check_exists():
            raise RuntimeError('Dataset not found.' +
                               ' You have to download it')
        """

        self.train_file = 'stackoverflow_train.h5'
        self.test_file = 'stackoverflow_test.h5'
        self.train = train

        self.vocab_tokens_size = 10000
        self.vocab_tags_size = 500


        # load data and targets
        self.raw_data, self.raw_targets, self.dict, self.client_list = self.load_file(self.root, self.train)

        # we can't enumerate the raw data, thus generating artificial data to cheat the divide_data_loader
        self.data = [0 for i in range(len(self.raw_data))]
        self.targets = [0 for i in range(len(self.raw_targets))]


        # First, get the token and tag dict
        self.vocab_tokens = self.create_token_vocab(self.vocab_tokens_size, self.root)
        self.vocab_tags = self.create_tag_vocab(self.vocab_tags_size, self.root)

        self.vocab_tokens_dict = {k: v for v, k in enumerate(self.vocab_tokens)}
        self.vocab_tags_dict = {k: v for v, k in enumerate(self.vocab_tags)}

    def __getitem__(self, index):
        """
        Args:xx
            index (int): Index

        Returns:
            tuple: (text, tags)
        """

        # get mapping

        [clientId, idx, clientLen] = self.raw_data[index]

        tokens = None
        tags = None
        failures = 0
        inFetch = True

        while inFetch:
            sample = self.client_list['examples'][clientId]
            token = sample['tokens'][idx]
            title = sample['title'][idx]
            tag = sample['tags'][idx]

            tokens = [self.vocab_tokens_dict[s] for s in (token.decode("utf-8").split() + title.decode("utf-8").split()) if s in self.vocab_tokens_dict]
            tags = [self.vocab_tags_dict[s] for s in tag.decode("utf-8").split('|') if s in self.vocab_tags_dict]

            if not tokens or not tags:
                failures += 1
                idx = (idx + 1) % clientLen
            else:
                inFetch = False

            if failures == 5:
                logging.info("====To many failures, system exit")
                system.exit(-1)

        # Lookup tensor
        tokens = torch.tensor(tokens, dtype=torch.long)
        tokens = F.one_hot(tokens, self.vocab_tokens_size).float()
        tokens = tokens.mean(0)

        tags = torch.tensor(tags, dtype=torch.long)
        tags = F.one_hot(tags, self.vocab_tags_size).float()
        tags = tags.sum(0)

        return tokens, tags

    def __mapping_dict__(self):
        return self.dict

    def __len__(self):
        return len(self.raw_data)

    @property
    def raw_folder(self):
        return self.root

    @property
    def processed_folder(self):
        return self.root

    @property
    def class_to_idx(self):
        return {_class: i for i, _class in enumerate(self.classes)}

    def _check_exists(self):
        return (os.path.exists(os.path.join(self.processed_folder,
                                            self.data_file)))

    def create_tag_vocab(self, vocab_size, path):
        """Creates vocab from `vocab_size` most common tags in Stackoverflow."""
        tags_file = "vocab_tags.txt"
        with open(path + tags_file, 'rb') as f:
            tags = pickle.load(f)
        return tags[:vocab_size]


    def create_token_vocab(self, vocab_size, path):
        """Creates vocab from `vocab_size` most common words in Stackoverflow."""
        tokens_file = "vocab_tokens.txt"
        with open(path + tokens_file, 'rb') as f:
            tokens = pickle.load(f)
        return tokens[:vocab_size]

    def load_file(self, path, is_train):

        text, target_tags = [], []
        mapping_dict = {}

        file_name = self.train_file if self.train else self.test_file
        
        # Load the traning data
        if self.train:
            train_file = h5.File(path + self.train_file, "r")
        else:
            train_file = h5.File(path + self.test_file, "r")

        count = 0
        clientCount = 0
        client_list = list(train_file['examples'])

        for clientId, client in enumerate(client_list):
            tags_list = list(train_file['examples'][client]['tags'])

            for idx in range(len(tags_list)):
                text.append([clientId, idx, len(tags_list)])
                target_tags.append(0)
                mapping_dict[count] = clientId

                count += 1

        return text, target_tags, mapping_dict, client_list

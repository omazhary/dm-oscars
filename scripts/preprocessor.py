#!/usr/bin/python

import csv
import random
import numbers
import decimal
import math
import numpy as np
from sklearn import preprocessing

# Author: Omar Elazhary <omazhary@gmail.com>
# License: MIT


class DataPreprocessor:
    """This class transforms your csv files into inputs suitable for use with
    scikit-learn."""

    def __init__(self, label_column_names_list, column_names_to_ignore_list,
                 csv_filename):
        """
        Instantiates a new DataPreprocessor object.
        Parameters:
            label_column_names_list - A list of column names that indicate
            class labels.
            column_names_to_ignore_list - A list of column names to ignore.
            csv_filename - The name of the source csv file.
        """
        self.features = []
        self.colmap = dict()
        self.class_labels = []
        self.labels = []
        self.class_label_index = []
        self.ignore = []
        self.csv_filename = ""
        self.column_headers = []
        self.features_numerical = []
        self.labels_numerical = []
        self.test_features = []
        self.test_labels = []
        self.csv_filename = csv_filename
        self.class_labels = label_column_names_list
        self.ignore = column_names_to_ignore_list
        for heading in self.class_labels:
            self.labels.append([])

    def preprocess(self):
        """
        Reads and preprocesses the data from a csv file to produce a large
        2d-arrary containing features, and a smaller 2d-array containing
        multiple labels where each is aligned with the features.
        """
        # Load data:
        counter = 0
        headers_processed = False
        temp_headers = []
        skippable_attributes = []
        should_skip = []

        with open(self.csv_filename, "rb") as dataset:
            entryreader = csv.reader(dataset, delimiter=',')
            for row in entryreader:
                if counter == 0:
                    # The first row is column headings (special treatment).
                    temp_headers = list(row)
                    for column in row:
                        self.colmap[column] = row.index(column)

                    skippable_attributes = list(self.ignore)
                    skippable_attributes = [
                            val for val in temp_headers
                            if val in skippable_attributes]
                    skippable_attributes.extend(self.class_labels)
                    skippable_attributes = [self.colmap[x] for x in
                                            skippable_attributes]

                    should_skip = [0] * len(temp_headers)
                    for x in range(len(skippable_attributes)):
                        should_skip[skippable_attributes[x]] = 1

                else:
                    # Need to separate features from ignored and class label
                    # fields.
                    data_row = []

                    for class_label in self.class_labels:
                        label_index = self.class_labels.index(class_label)
                        column_value = row[self.colmap[class_label]]
                        self.labels[label_index].append(
                                self.process_value(column_value))

                    # print 'here'
                    for index, value in enumerate(row):
                        # if index not in skippable_attributes:
                        if should_skip[index] == 0:
                            data_row.append(self.process_value(value))
                            if not headers_processed:
                                self.column_headers.append(temp_headers[index])

                    # print 'there'
                    headers_processed = True
                    self.features.append(data_row)
                counter += 1

    def split_features(self, test=False):
        """
        Splits the already preprocessed feature matrix vertically instead of
        horizontally, so that you get a single list per feature, perfectly
        aligned with the class labels. Requires that the features already be
        preprocessed.
        """
        # Initialize the result arrays:
        feat_in = []
        result = []
        if test:
            feat_in = self.test_features
        else:
            feat_in = self.features
        for feature in feat_in[0]:
            result.append([])

        for index1, value1 in enumerate(feat_in):
            for index2, value2 in enumerate(feat_in[index1]):
                result[index2].append(value2)

        return result

    def numerify(self, skip_scaling=[]):
        """
        Converts all non-numerical attributes (features and labels) into
        numerical attributes.
        Parameters:
            skip_scaling - List of feature indices for whom no scaling should
            occur.
        """
        skip_scaling.sort(reverse=True)
        # For features:
        temp = self.split_features()
        skipped = []
        skipped_indexes = []
        for i in range(len(temp)):
            self.features_numerical.append([])
        for index, feature_vector in enumerate(temp):
            test_index = 0
            if (feature_vector[test_index] == ''):
                test_index = random.randrange(1, len(feature_vector))
            if (not isinstance(feature_vector[test_index], numbers.Number) and
                    not isinstance(feature_vector[test_index],
                                   decimal.Decimal)):
                encoder = preprocessing.LabelEncoder()
                encoder.fit(feature_vector)
                self.features_numerical[index] = encoder.transform(
                        feature_vector)
            else:
                self.features_numerical[index] = list(feature_vector)
            if index in skip_scaling:
                skipped.append(feature_vector)
                skipped_indexes.append(index)
        for index in skipped_indexes:
            del self.features_numerical[index]
        # Rearrange features into rows:
        self.features_numerical = map(list, zip(*self.features_numerical))
        # For labels:
        for label_vector in self.labels:
            test_index = 0
            if (label_vector[test_index] == ''):
                test_index = random.randrange(1, len(label_vector))
            if (not isinstance(label_vector[test_index], numbers.Number) and
                    not isinstance(label_vector[test_index],
                                   decimal.Decimal)):
                encoder = preprocessing.LabelEncoder()
                encoder.fit(label_vector)
                self.labels_numerical.append(encoder.transform(label_vector))
            else:
                self.labels_numerical.append(list(label_vector))
        # Do cleanup (deal with missing values):
        janitor = preprocessing.Imputer(missing_values=np.NaN,
                                        strategy='most_frequent')
        self.features_numerical = janitor.fit_transform(
                self.features_numerical).tolist()
        scaler = preprocessing.StandardScaler()
        self.features_numerical = scaler.fit_transform(
                self.features_numerical).tolist()
        for skip in skipped:
            for index, feature in enumerate(skip):
                self.features_numerical[index].append(feature)

    def add_feature(self, new_feat):
        """
        Adds a new list representing a feature and its values to the matrix of
        existing features. The list must be of a length equal to that of the
        total tuples in the dataset and aligned with it.
        Parameters:
            new_feat - The new feature vector to be added.
        """
        if not isinstance(new_feat, list):
            raise TypeError('Invalid parameter type. Expecting type: list')
        if len(new_feat) != len(self.features):
            raise IndexError('Invalid list length')
        # Add the feature values to the tuples (assuming alignment)
        for index1, vector1 in enumerate(self.features):
            self.features[index1].append(new_feat[index1])

    def create_test_set(self, test_indices):
        """
        Pulls out specific rows from the feature set to create a test set. The
        test vectors are then stored in test_features and test_labels. It makes
        sense to call this after the "numerify" function.
        Parameters:
            test_indices - A list of indices that should be used as a test set.
        """
        test_indices = sorted(test_indices, reverse=True)
        for index in test_indices:
            self.test_features.append(self.features_numerical[index])
            del self.features_numerical[index]
        for label_index, label in enumerate(self.labels_numerical):
            self.test_labels.append([])
            for index in test_indices:
                self.test_labels[label_index].append(
                                self.labels_numerical[label_index][index])
                del self.labels_numerical[label_index][index]

    def randomize_test_set(self, test_data_percent, label_index,
                           balanced=False):
        """
        Samples a test set out of the existing feature and label sets without
        replacement. The size of the testset is the percentage given of the
        original dataset rounded up to the nearest tuple. If balanced, the
        distribution of the labels will be mirrored in the test set, random
        otherwise. The extraction occurs on the numerical sets.
        Parameters:
            test_data_percent - The percentage (0-1) of data to be used from
            the original dataset.
            label_index - The index of the label vector to be tested.
            balanced - Boolean indicating if the distribution should be
            mirrored.
        """
        test_data_size = math.ceil(test_data_percent * len(self.features))
        indexes = []  # Houses indices for test tuples.
        if not balanced:
            indexes = random.sample(range(0, len(self.features_numerical)),
                                    test_data_size)
        else:
            # Get unique class distributions:
            dist_values = dict()
            dist_indices = dict()
            for index, label in enumerate(self.labels_numerical[label_index]):
                if label in dist_values:
                    dist_values[label] += 1
                    dist_indices[label].append(index)
                else:
                    dist_values[label] = 1
                    dist_indices[label] = [index]
            for key, count in dist_values.iteritems():
                dist_values[key] = int(math.ceil(test_data_percent *
                                       len(dist_indices[key])))
                indexes.extend(random.sample(range(0, len(dist_indices[key])),
                                             dist_values[key]
                                             )
                               )
        # Sort the indexes so that removing the items is painless:
        indexes.sort(reverse=True)
        for index in indexes:
            self.test_features.append(self.features_numerical[index])
            self.test_labels.append(
                            self.labels_numerical[label_index][index])
            del self.features_numerical[index]
            del self.labels_numerical[label_index][index]

    # Helper Functions:
    def is_float(self, value):
        try:
            float(value)
            return True
        except:
            return False

    def is_int(self, value):
        try:
            int(value)
            return True
        except:
            return False

    def is_boolean(self, value):
        try:
            bool(value)
            return True
        except:
            return False

    def process_value(self, value):
        if self.is_int(value):
            return int(value)
        elif self.is_float(value):
            return float(value)
        elif value == '':
            return np.NaN
        else:
            return value

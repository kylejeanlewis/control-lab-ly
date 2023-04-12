"""
This sub-package imports the base class for image classifiers
and the class for cascade classifiers.

Classes:
    Classifier (ABC)
    CascadeClassifier (Classifier)
"""
from .classifier_utils import Classifier, CascadeClassifier

from controllably import include_this_module
include_this_module(get_local_only=False)
#!/usr/bin/env python3

import argparse
from os import path

from Tools import DictList, EvaluationResult, TransitiveKeyList

FALSE_POSTITIVES_FILES = './false-positives'
SIMILAR_PATCHES_FILE = './similar_patch_list'
EVALUATION_RESULT_FILE = './evaluation-result'
INTERACTIVE_THRESHOLD = 0.80
AUTOACCEPT_THRESHOLD = 0.9
DIFF_LENGTH_RATIO_THRESHOLD = 0.5

parser = argparse.ArgumentParser(description='Interactive Rating: Rate evaluation results')
parser.add_argument('-fp', dest='fp_filename', default=FALSE_POSTITIVES_FILES, help='False Positive PKL filename')
parser.add_argument('-sp', dest='sp_filename', default=SIMILAR_PATCHES_FILE, help='Similar Patches filename')
parser.add_argument('-er', dest='er_filename', default=EVALUATION_RESULT_FILE, help='Evaluation Result PKL filename')
parser.add_argument('-aat', dest='aa_threshold', type=float, default=AUTOACCEPT_THRESHOLD, help='Autoaccept Threshold')
parser.add_argument('-it', dest='it_threshold', type=float, default=AUTOACCEPT_THRESHOLD, help='Interactive Threshold')
parser.add_argument('-dlr', dest='dlr_threshold', type=float, default=DIFF_LENGTH_RATIO_THRESHOLD, help='Diff Length Ratio Threshold')

args = parser.parse_args()

# Load already known positives and false positives
similar_patches = TransitiveKeyList.from_file(args.sp_filename)
human_readable = not args.fp_filename.endswith('.pkl')
false_positives = DictList.from_file(args.fp_filename, human_readable=human_readable)

evaluation_result = EvaluationResult.from_file(args.er_filename)
evaluation_result.interactive_rating(similar_patches, false_positives,
                                     args.aa_threshold, args.it_threshold, args.dlr_threshold)

similar_patches.to_file(args.sp_filename)

fp_filename = args.fp_filename
if not human_readable:
    fp_filename = path.splitext(fp_filename)[0]
false_positives.to_file(fp_filename)
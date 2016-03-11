#!/usr/bin/env python3

import argparse
from git import Repo
import re
from termcolor import colored

from config import *
from EquivalenceClass import EquivalenceClass
from PatchEvaluation import evaluate_patch_list, EvaluationResult
from PatchStack import cache_commit_hashes, parse_patch_stack_definition, get_commit_hashes, get_commit

EVALUATION_RESULT_FILENAME = './evaluation-result.pkl'


def _evaluate_patch_list_wrapper(args):
    orig, cand = args
    return evaluate_patch_list(orig, cand)

# Startup
parser = argparse.ArgumentParser(description='Analyse stack by stack')
parser.add_argument('-er', dest='evaluation_result_filename', default=EVALUATION_RESULT_FILENAME, help='Evaluation result filename')
parser.add_argument('-sp', dest='sp_filename', default=SIMILAR_PATCHES_FILE, help='Similar Patches filename')

args = parser.parse_args()

# Load patch stack definition
repo = Repo(REPO_LOCATION)
patch_stack_list = parse_patch_stack_definition(PATCH_STACK_DEFINITION)

# Load and cache upstream commits
upstream_candidates = get_commit_hashes(repo, UPSTREAM_MIN, UPSTREAM_MAX)
upstream_candidates -= COMMITHASH_BLACKLIST
cache_commit_hashes(upstream_candidates, parallelize=True)

# Load similar patches file
similar_patches = EquivalenceClass.from_file(args.sp_filename)

sys.stdout.write('Determining patch stack representative system...')
sys.stdout.flush()
# Get the complete representative system
# The lambda compares two patches of an equivalence class and chooses the one with
# the later release version
representatives = similar_patches.get_representative_system(
    lambda x, y: patch_stack_list.is_stack_version_greater(patch_stack_list.get_stack_of_commit(x),
                                                           patch_stack_list.get_stack_of_commit(y)))

print(colored(' [done]', 'green'))
cache_commit_hashes(representatives, parallelize=True)

print('Searching for cherry-picks...')
cherry_picks = EvaluationResult()
cherry_picks.set_universe(set())
cherry_regex = re.compile(r'.*pick.*', re.IGNORECASE)
sha1_regex = re.compile(r'\b([0-9a-fA-F]{5,40})\b')
for commit_hash in representatives:
    commit = get_commit(commit_hash)
    for line in commit.message:
        if cherry_regex.match(line):
            sha_found = sha1_regex.search(line)
            if not sha_found:
                continue
            upstream_hash = sha_found.group(1)
            if upstream_hash in upstream_candidates:
                cherry_picks[commit_hash] = [(upstream_hash, 1.0, 1.0, 1.0)]
            else:
                print('Found cherry-pick: %s <-> %s but upstream is not in upstream candidates list.' % (commit_hash, upstream_hash))
print('Done. Found %d cherry-picks' % len(cherry_picks))

print('Starting evaluation.')
evaluation_result = evaluate_patch_list(representatives, upstream_candidates,
                                        parallelize=True, verbose=True,
                                        cpu_factor = 0.5)
print('Evaluation completed.')

evaluation_result.merge(cherry_picks)

# We don't have a universe in this case
evaluation_result.set_universe(set())
evaluation_result.to_file(args.evaluation_result_filename)

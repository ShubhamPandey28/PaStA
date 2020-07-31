"""
PaStA - Patch Stack Analysis

Author:
  Shubhamkumar Pandey <b18194@students.iitmandi.ac.in>

This work is licensed under the terms of the GNU GPL, version 2.  See
the COPYING file in the top-level directory.
"""

import os
import sys
import argparse
import pickle

from tqdm import tqdm
from collections import defaultdict, Counter
from logging import getLogger

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pypasta import *
from pypasta.LinuxMailCharacteristics import email_get_recipients
from pypasta.Repository.Patch import Diff

log = getLogger(__name__[-15:])



def train_model(config, thres_prob):
	repo = config.repo
	RECIPIENTS = defaultdict(Counter)
	for message_id in tqdm(repo.mbox.get_ids(time_window=config.mbox_time_window)):
		patch = repo[message_id]
		mail = repo.mbox.get_messages(message_id)[0]
		recipients = email_get_recipients(mail)
		for filename in patch.diff.affected:
			for recipient in recipients:
				RECIPIENTS[filename][recipient] += 1

	for filename, ctr in RECIPIENTS.items():
		total_patches = sum(ctr.values())
		for recipient in ctr.keys():
			ctr[recipient] /= total_patches
		ctr = sorted(ctr.items(), key = lambda x :x[1], reverse=True)
		recipients = set()
		probability = 0
		for recipient_id, prob in ctr:
			if probability >= thres_prob:
				break
			recipients.add(recipient_id)
			probability += prob
		RECIPIENTS[filename] = recipients

	return RECIPIENTS



def predict_maintainers(config, argv):

	parser = argparse.ArgumentParser(prog='predict', description='Predict recipients of the patch file passed')

	parser.add_argument('-tp', dest='thres_prob', metavar='thresold', default=0.7, type=float, 
						help='Thresold probability for predicting the patch recipients')
	parser.add_argument('-train', dest='_train', action="store_true",
						help='Train the model before prediction')
	parser.add_argument('-modelpath', dest='f_model', metavar='model', default=None, type=str,
						help='Path to the model .pkl file')
	parser.add_argument('-save', dest='f_saveto', metavar='saveto', default=None, type=str,
						help='Path to the trained model .pkl file')
	parser.add_argument('-patch', dest='f_patch', metavar='patch', type=str,
						help='Path to the patch file')
	parser.add_argument('-out', dest='f_out', metavar='outpath', type=str, default=None,
						help='Provide a path to output file containing the list of maintainers related to the patch.')

	args = parser.parse_args(argv)
	repo = config.repo
	repo.register_mbox(config)

	if args._train:
		log.info("Training model")
		RECIPIENTS = train_model(config, args.thres_prob)
		if args.f_saveto:
			args.f_saveto = os.path.join(os.getcwd(), args.f_saveto)
			pickle.dump(RECIPIENTS, open(args.f_saveto, 'wb'))

	elif args.f_model:
		args.f_model = os.path.join(os.getcwd(), args.f_model)
		log.info(f"Loading model {args.f_model}")
		RECIPIENTS = pickle.load(open(args.f_model, "rb"))

	else:
		raise ValueError("Either train the model or provide path to previuosly trained model.")

	diff = Diff(open(os.path.join(os.getcwd(),args.f_patch), "r").readlines())

	recipients = set()
	for filename in diff.affected:
		if filename in RECIPIENTS:
			recipients |= RECIPIENTS[filename]

	if not args.f_out:
		args.f_out = os.path.join(os.getcwd(), f'MAINTAINER-LIST-FOR-PATCH--{args.f_patch}')

	with open(args.f_out, 'w') as f:
		f.write('\n'.join(recipients))

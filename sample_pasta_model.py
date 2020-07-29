from pypasta import *
from collections import defaultdict, Counter
from tqdm import tqdm
from pypasta.LinuxMailCharacteristics import email_get_recipients
from sklearn.model_selection import train_test_split


class SamplePastaModel:

    def __init__(self, project_name : str):
        self.config = Config(project_name)
        self.repo = self.config.repo
        self.repo.register_mbox(self.config)
        self._RECIPIENTS = None

    def get_actual_recipients(self, message_id : str) -> list:
        mail = self.repo.mbox.get_messages(message_id)[0]
        recipients = email_get_recipients(mail)
        return recipients

    def get_suggested_recipients(self, patch : PatchMail) -> list:
        recipients = []
        for filename in patch.diff.affected:
            if filename in self._RECIPIENTS:
                recipients += self._RECIPIENTS[filename]
        return recipients

    def fit(self, train_ids : list, thresold_probability : float = 0.7):
        self._RECIPIENTS = defaultdict(lambda: Counter())
        cnt = 0 # counting for making sure
        for message_id in tqdm(train_ids):  
            if message_id in self.repo:
                patch = self.repo[message_id]
                recipients = self.get_actual_recipients(message_id)
                for filename in patch.diff.affected:
                    for recipient in recipients:
                        self._RECIPIENTS[filename][recipient] += 1
                cnt += 1
        
        print(f"Processed {cnt} patches")

        for filename in self._RECIPIENTS.keys():
            total_patches = sum(self._RECIPIENTS[filename].values())
            for recipient in self._RECIPIENTS[filename].keys():
                self._RECIPIENTS[filename][recipient] /= total_patches
            self._RECIPIENTS[filename] = sorted(self._RECIPIENTS[filename].items(), key = lambda x :x[1], reverse=True)
            recipient_list = []
            probability = 0
            for x, p in self._RECIPIENTS[filename]:
                if probability >= thresold_probability:
                    break
                recipient_list.append(x)
                probability += p
            self._RECIPIENTS[filename] = recipient_list

    def predict_one(self, patch : PatchMail) -> list:
        if self._RECIPIENTS:
            return self.get_suggested_recipients(patch)
        raise Exception("The model has not been trained.\n First train the model.")

    def test(self):
        train_ids, test_ids = train_test_split(list(self.repo.mbox.get_ids(
            time_window=self.config.mbox_time_window)), random_state=42, test_size=0.3)
        print("Training the model...")
        self.fit(train_ids)
        mean_accuracy = 0
        count_valid = 0
        print("Testing the model...")
        for message_id in tqdm(test_ids):
            if message_id in self.repo:
                patch = self.repo[message_id]
                suggested_recipients = set(self.predict_one(patch))
                actual_recipients = set(self.get_actual_recipients(message_id))
                mean_accuracy += len(actual_recipients.intersection(suggested_recipients)) / len(actual_recipients)
                count_valid += 1
        mean_accuracy /= count_valid
        print(f" Ended with an accuracy of {mean_accuracy} ")
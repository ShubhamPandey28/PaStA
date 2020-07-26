from pypasta import *
from pypasta.LinuxMailCharacteristics import email_get_recipients

from tqdm import tqdm
import email

cfg = Config("linux")
repo = cfg.repo

mboxes = Mbox(cfg)

def hash_tuple(mail_id_1 : str, mail_id_2 : str) -> str:
    return min(mail_id_1, mail_id_2) + "##" + max(mail_id_1, mail_id_2)

def mail_id_is_bot(mail_id : str) -> bool:
    if mail_id in LinuxMailCharacteristics.BOTS | LinuxMailCharacteristics.POTENTIAL_BOTS:
        return True
    return False

joint_count = dict()
count = dict()

for box in mboxes.mboxes:
    for message_id in tqdm(box.get_ids()):
        mail = mboxes.get_messages(message_id)[0]
        break
        try:
            mail, payload = PatchMail.extract_patch_mail(mail)

        except ValueError:
            #print(f"{message_id} is not a patch.")
            continue

        recipients = list(email_get_recipients(mail))

        for i in range(len(recipients)):
            mail_id_1 = recipients[i]
            if mail_id_is_bot(mail_id_1):
                continue
            if mail_id_1 in count:
                count[mail_id_1] +=1
            else:
                count[mail_id_1] = 1
            for j in range(i+1, len(recipients)):
                mail_id_2 = recipients[j]
                if mail_id_is_bot(mail_id_2):
                    continue
                
                if hash_tuple(mail_id_1, mail_id_2) in joint_count:
                    joint_count[hash_tuple(mail_id_1, mail_id_2)] += 1
                else:
                    joint_count[hash_tuple(mail_id_1, mail_id_2)] = 1

import graphviz

graph = graphviz.Digraph(comment="Probability graph of reciepients", format='pdf')

thresold_probability = 0.8

def get_conditional_probability(mail_id_1, mail_id_2):
    return joint_count[hash_tuple(mail_id_1, mail_id_2)] / count[mail_id_1]

print("plotting graph ...")
for key in tqdm(joint_count.keys()):
    mail_id_1, mail_id_2 = key.split('##')
    graph.node(mail_id_1)
    graph.node(mail_id_2)
    if get_conditional_probability(mail_id_1, mail_id_2) > thresold_probability:
        graph.edge(mail_id_1, mail_id_2, label=f"{get_conditional_probability(mail_id_1, mail_id_2)}")
    if get_conditional_probability(mail_id_2, mail_id_1) > thresold_probability:
        graph.edge(mail_id_2, mail_id_1, label=f"{get_conditional_probability(mail_id_2, mail_id_1)}")

print(graph)
graph.render("out.pdf",format="pdf")
import pandas as pd

df = pd.read_csv("data/jigsaw-toxic-comment-classification-challenge/train.csv")
df["ones"] = 1
toxic_columns = ['toxic', 'severe_toxic', 'obscene', 'threat',
       'insult', 'identity_hate']

toxic_row = df[df[toxic_columns].any(axis='columns')][["comment_text", "ones"]].reset_index(drop=True)
toxic_row = toxic_row.rename(columns={"ones": "toxic"})

normal_row = df[~df[toxic_columns].any(axis='columns')][["comment_text", "toxic"]].reset_index(drop=True)

df_merged = toxic_row.append(normal_row, ignore_index=True).sample(frac=1).reset_index(drop=True)

df_merged.to_csv("data/train.csv", index=False, header=False)
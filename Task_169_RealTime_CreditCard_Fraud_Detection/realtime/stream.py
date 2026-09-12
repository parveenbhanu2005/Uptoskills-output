import pandas as pd
import time


def transaction_stream(csv_file):

    df = pd.read_csv(csv_file)

    for _, row in df.iterrows():

        yield row.to_dict()

        time.sleep(1)
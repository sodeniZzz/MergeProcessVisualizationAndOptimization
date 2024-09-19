import requests
import pandas as pd
import numpy as np


def fetchDataFromClickHouse():
    clickhouse_server_url = "http://127.0.0.1:8123/?query=SELECT%20*%20FROM%20system.part_log%20FORMAT%20JSON"

    try:
        response = requests.get(clickhouse_server_url)
        data = response.json()["data"]

        df = pd.DataFrame(data)
        df["event_time"] = pd.to_datetime(df["event_time"])
        df = df[df["event_type"] != "RemovePart"]
        df = df.sort_values(by="event_time")

        return df

    except Exception as e:
        print(f"Error: {e}")
        raise


def calculate_metrics(df):
    df["ProfileEvents_WriteBytes"] = df["ProfileEvents"].apply(
        lambda x: int(x.get("WriteBufferFromFileDescriptorWriteBytes", 0))
    )
    total_written_bytes = df["ProfileEvents_WriteBytes"].sum()
    insert_written_bytes = df[df["event_type"] == "NewPart"][
        "ProfileEvents_WriteBytes"
    ].sum()

    write_amplification = total_written_bytes / insert_written_bytes
    print(f"Write Amplification: {write_amplification:.5f}")

    current_chunk_count = 0
    chunk_counts = []
    for _, row in df.iterrows():
        if row["event_type"] == "NewPart":
            current_chunk_count += 1
        elif row["event_type"] == "MergeParts":
            current_chunk_count -= len(row["merged_from"]) - 1

        chunk_counts.append(current_chunk_count)

    print(f"Average number of chunks: {np.mean(chunk_counts):.5f}")


if __name__ == "__main__":
    df = fetchDataFromClickHouse()
    calculate_metrics(df)

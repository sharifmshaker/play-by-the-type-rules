import os
import typing as t
from pathlib import Path 
import datasets 
import sqlite3
import pysbd
import pandas as pd
from datasets import Dataset

from .dataset_utils import table_to_df

def load_hybridqa(split: str, num_examples: int = None, num_proc: int = 12) -> datasets.Dataset:
    seg = pysbd.Segmenter(language="en", clean=False)
    
    def add_db_path(example) -> str:
        db_path = Path(os.environ["DB_DIR"]) / "hybridqa" / f"{example['table_id']}.db"
        example["db_path"] = str(db_path)
        if db_path.is_file():
            return example

        # Aggregate context to dataframes
        table_rows = [i["value"] for i in example["table"]["rows"]]
        table_header = example["table"]["header"]
        table_df = table_to_df(
            {"header": table_header, "rows": table_rows},
            normalize=True,
            add_row_id=False,
        )
        document_rows = []
        for row in example["table"]["rows"]:
            for url_data in row["urls"]:
                for url, summary in zip(url_data["url"], url_data["summary"]):
                    title = url.split("/")[-1].replace("_", " ")
                    for sent in seg.segment(summary):
                        # Add each sentence as its own row
                        document_rows.append([title, sent])
        # Don't normalize the documents table
        document_df = table_to_df(
            {"header": ["title", "content"], "rows": document_rows},
            normalize=False,
            lower_case=False,
            add_row_id=False,
        )

        # Add dataframes to sqlite database
        if not db_path.parent.is_dir():
            db_path.parent.mkdir(parents=True)
        sqlite_conn = sqlite3.connect(db_path)
        table_df.to_sql("w", sqlite_conn, index=False, if_exists="replace")
        document_df.to_sql("documents", sqlite_conn, index=False, if_exists="replace")
        sqlite_conn.close()

        return example


    dataset = datasets.load_dataset(
        str(Path(__file__).parent / "hybridqa"),
        trust_remote_code=True,
    )[split]
    if num_examples is not None:
        dataset = dataset.select(range(num_examples))
    dataset = dataset.map(add_db_path, num_proc=num_proc)
    return dataset

def load_musique(split: str, num_examples: int = None, num_proc: int = 12) -> datasets.Dataset:
    if split == 'validation': 
        dataset = Dataset.from_pandas(pd.read_json(Path(__file__).parent / "musique/musique_ans_v1.0_dev.jsonl", lines=True)) 
    elif split == 'train':
         dataset = Dataset.from_pandas(pd.read_json(Path(__file__).parent / "musique/musique_ans_v1.0_train.jsonl", lines=True)) 
    else:
        raise ValueError(f"Unknown split {split}")
        
    def add_db_path(example) -> str:
        db_path = Path(os.environ["DB_DIR"]) / "musique" / f"{example['id']}.db"
        example["db_path"] = str(db_path)
        if db_path.is_file():
            return example
        docs_df = pd.DataFrame([(i['title'], i['paragraph_text']) for i in example['paragraphs']], columns=["title", "content"])
         # Add dataframes to sqlite database
        if not db_path.parent.is_dir():
            db_path.parent.mkdir(parents=True)
        sqlite_conn = sqlite3.connect(db_path)
        docs_df.to_sql("documents", sqlite_conn, index=False, if_exists="replace")
        sqlite_conn.close()
        return example 
        
    if num_examples is not None:
        dataset = dataset.select(range(num_examples))
    dataset = dataset.map(add_db_path, num_proc=num_proc)
    return dataset
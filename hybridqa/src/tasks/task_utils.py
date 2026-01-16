import typing as t 
import evaluate
import datasets
from pathlib import Path

from src.args import Task
from src.tasks.load_datasets import load_hybridqa, load_musique

def load_task(task: Task, split: str, num_examples: t.Optional[int] = None) -> t.Tuple[datasets.Dataset, evaluate.EvaluationModule]:
    load_metric = lambda p: evaluate.load(
        p, keep_in_memory=True
    )
    if task == 'hybridqa':
        return (
            load_hybridqa(split, num_examples=num_examples, num_proc=6),
            load_metric(str(Path(__file__).parent / "../metrics/hybridqa")),
        )
    elif task == 'musique':
        return (
            load_musique(split, num_examples=num_examples, num_proc=6),
            load_metric(str(Path(__file__).parent / "../metrics/musique"))
        )
    else:
        raise ValueError(f"Unknown task {task}")

def get_serialized_hybridqa_db(example: dict) -> str:
    from blendsql.db import SQLite
    db = SQLite(example["db_path"])
    table_to_description = {
        "w": f"`w` is sourced from the `{'_'.join(example['table_id'].split('_')[:-1])}` Wikipedia table."
    }
    return db.to_serialized(question=example['question'], num_rows=100, use_tables=["w"], include_content=['w'], use_bridge_encoder=True, table_to_description=table_to_description)
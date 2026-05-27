from dataclasses import dataclass, field
import json
import typing as t 


Task = t.Literal['hybridqa']

@dataclass 
class BlendSQLArguments:
    blendsql_model_name_or_path: str = field(
        metadata={"help": "Model to use in executing a BlendSQL query."}, default=None
    )
    infer_gen_constraints: bool = field(default=True)
    enable_constrained_decoding: bool = field(default=True)
    llmmap_args: t.Optional[t.Union[dict, str]] = field(default=None)
    llmsearchmap_args: t.Optional[t.Union[dict, str]] = field(default=None)
    llmqa_args: t.Optional[t.Union[dict, str]] = field(default=None)

    def __post_init__(self):
        """Convert json str to dict"""
        for attrib in ['llmmap_args', 'llmsearchmap_args', 'llmqa_args']:
            v = getattr(self, attrib)
            if isinstance(v, str):
                setattr(self, attrib, json.loads(v))

@dataclass 
class BaselineArgs:
    searcher_model_name_or_path: str = field(default=None)
    searcher_k: int = field(default=None)
    bm25_weight: float = field(default=None)

@dataclass 
class ExperimentArgs:
    mode: t.Literal['baseline', 'baseline-no-context', 'baseline-all-context', 'program-synthesis', 'program-synthesis-grammar-prompting', 'program-synthesis-rust-references'] = field()
    task: Task = field()
    split: str = field()
    output_dir: str = field()
    num_examples: t.Optional[int] = field(default=None)
    model_name_or_path: t.Optional[str] = field(default=None)
    parsing_service: t.Optional[str] = field(default=None)
    parsing_service_model_name: t.Optional[str] = field(default=None)
    use_guided_grammar: t.Optional[bool] = field(default=False)
    use_documentation: t.Optional[bool] = field(default=True)
    generation_path: t.Optional[str] = field(default=None)
    use_fewshot_examples: t.Optional[bool] = field(default=True)


@dataclass 
class TrainArgs:
    task: Task = field()
    split: str = field()
    mode: t.Literal[
        "baseline",
        "program-synthesis",
    ] = field()
    output_dir: str = field()
    model_name_or_path: t.Optional[str] = field()
    rejection_sampling: t.Optional[bool] = field()
    generation_path: t.Optional[str] = field(default=None)
    blendsql_model_path: t.Optional[str] = field(default=None)
    training_args: t.Optional[str] = field(default=None)
    num_examples: t.Optional[int] = field(default=5000)

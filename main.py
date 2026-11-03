from Core.GraphRAG import GraphRAG
from Option.Config2 import Config
import argparse
import os
import asyncio
from pathlib import Path
from shutil import copyfile
from Data.QueryDataset import RAGQueryDataset
from Data.ModernAluminumDataset import ModernAluminumRAGDataset
import pandas as pd
from Core.Utils.Evaluation import Evaluator
from Core.Common.Logger import logger
from time import perf_counter



def check_dirs(opt, option_path):
    # For each query, save the results in a separate directory
    result_dir = os.path.join(opt.working_dir, opt.exp_name, "Results")
    # Save the current used config in a separate directory
    config_dir = os.path.join(opt.working_dir, opt.exp_name, "Configs")
    # Save the metrics of entire experiment in a separate directory
    metric_dir = os.path.join(opt.working_dir, opt.exp_name, "Metrics")
    os.makedirs(result_dir, exist_ok=True)
    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(metric_dir, exist_ok=True)
    opt_name = option_path.name
    basic_name = Path(__file__).resolve().parent / "Option" / "Config2.yaml"
    copyfile(option_path, os.path.join(config_dir, opt_name))
    copyfile(basic_name, os.path.join(config_dir, "Config2.yaml"))
    return result_dir


def wrapper_query(query_dataset, digimon, result_dir, query_limit=10):
    all_res = []

    # Keep the default command suitable for an interactive local smoke test.
    # The full dataset remains available by changing this explicit limit.
    dataset_len = len(query_dataset) if query_limit is None or query_limit <= 0 else min(query_limit, len(query_dataset))
    logger.info("Starting question answering for the first {}/{} questions", dataset_len, len(query_dataset))

    for i in range(dataset_len):
        query = query_dataset[i]
        question = query["question"]
        logger.info("[Query {}/{}] Question: {}", i + 1, dataset_len, question)
        started_at = perf_counter()
        res = asyncio.run(digimon.query(question))
        query["output"] = res
        all_res.append(query)
        logger.info(
            "[Query {}/{}] Answer (elapsed_s={:.2f}):\n{}",
            i + 1, dataset_len, perf_counter() - started_at, res,
        )

    all_res_df = pd.DataFrame(all_res)
    save_path = os.path.join(result_dir, "results.json")
    all_res_df.to_json(save_path, orient="records", lines=True)
    logger.info("Saved {} query results to {}", len(all_res), save_path)
    return save_path


async def wrapper_evaluation(path, opt, result_dir):
    eval = Evaluator(path, opt.dataset_name, config=opt)
    res_dict = await eval.evaluate()
    save_path = os.path.join(result_dir, "metrics.json")
    with open(save_path, "w") as f:
        f.write(str(res_dict))


if __name__ == "__main__":

    # with open("./book.txt") as f:
    #     doc = f.read()

    parser = argparse.ArgumentParser()
    parser.add_argument("-opt", type=str, help="Path to option YMAL file.")
    parser.add_argument("-dataset_name", type=str, help="Name of the dataset.")
    parser.add_argument("--qa_file", type=str, default=None, help="Optional external QA JSONL for modern aluminum.")
    parser.add_argument("--query_limit", type=int, default=10, help="Questions to answer; 0 means all.")
    parser.add_argument("--skip_query", action="store_true", help="Build/index graph only.")
    parser.add_argument("--evaluate", action="store_true", help="Run legacy automatic metrics only when a suitable gold QA set is supplied.")
    args = parser.parse_args()

    option_path = Path(args.opt).resolve()
    opt = Config.parse(option_path, dataset_name=args.dataset_name)
    repo_root = Path(__file__).resolve().parent
    if args.dataset_name == "modern_aluminum_kg_corpus_v2":
        # Keep graph/index/result artefacts separate from the immutable OCR
        # corpus even though the legacy Config parser normally uses a folder
        # named after the dataset under the repository root.
        opt.working_dir = str(repo_root / "outputs" / args.dataset_name)
    digimon = GraphRAG(config=opt)
    result_dir = check_dirs(opt, option_path)

    modern_dir = repo_root / "modern_aluminum_kg_corpus_v2"
    if args.dataset_name == "modern_aluminum_kg_corpus_v2":
        # The modern corpus is a first-class project asset, not a converted
        # legacy Corpus.json dataset.  Its source chunk IDs reach DocChunk.
        query_dataset = ModernAluminumRAGDataset(modern_dir, args.qa_file)
    else:
        query_dataset = RAGQueryDataset(data_dir=os.path.join(opt.data_root, opt.dataset_name))
    corpus = query_dataset.get_corpus()
    # corpus = corpus[:10]

    asyncio.run(digimon.insert(corpus))

    if not args.skip_query and len(query_dataset):
        save_path = wrapper_query(query_dataset, digimon, result_dir, args.query_limit)
        # Candidate benchmark items are deliberately not silently turned into
        # final quality metrics.  Legacy evaluation stays opt-in.
        if args.evaluate:
            asyncio.run(wrapper_evaluation(save_path, opt, result_dir))
    elif not args.skip_query:
        logger.warning("No QA file found; graph was built but no query/evaluation stage was run.")

    # for train_item in dataloader:

    # a = asyncio.run(digimon.query("Who is Fred Gehrke?"))

    # asyncio.run(digimon.query("Who is Scrooge?"))

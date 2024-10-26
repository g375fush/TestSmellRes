"""
解析対象のコミットハッシュを固定するために csv に記録する．
"""
import csv
from pathlib import Path

from tqdm import tqdm

from global_var import deadline
from repo import Repo

all_commit_hashes = []

repo_path_list = list(Path('../repo').resolve(strict=True).glob('*'))
repo_path_list.sort()
for repo_path in tqdm(repo_path_list):
    repo = Repo(repo_path)
    commit_hashes = repo.get_commit_hashes(until=deadline)
    all_commit_hashes.append(commit_hashes)

with Path('../result/commit_hashes.csv').open('w', encoding='utf-8-sig',
                                              newline='') as f:
    writer = csv.writer(f)
    writer.writerows(all_commit_hashes)

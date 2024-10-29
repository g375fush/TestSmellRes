"""
解析対象のコミットハッシュを固定するために csv に記録する．
"""
import csv
from pathlib import Path

import git.exc
from tqdm import tqdm

from global_var import deadline
from repo import Repo

all_commit_hashes = []

target_list = list(Path('../repo').resolve(strict=True).glob('*'))
target_list.sort()
for repo_prefix in tqdm(target_list):
    repo_name = repo_prefix.glob('*').__next__().stem
    repo_path = repo_prefix / repo_name
    repo = Repo(repo_path)
    try:
        repo.checkout_head_commit()
    except git.exc.GitCommandError:
        continue
    commit_hashes = repo.get_commit_hashes(until=deadline)
    all_commit_hashes.append([repo_name] + commit_hashes)

with Path('../result/commit_hashes.csv').open('w', encoding='utf-8-sig',
                                              newline='') as f:
    writer = csv.writer(f)
    writer.writerows(all_commit_hashes)

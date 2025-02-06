"""
解析対象のコミットハッシュを固定するために csv に記録する．
"""
import json
from pathlib import Path

from tqdm import tqdm

from global_var import deadline
from repo import Repo


this_file_name = Path(__file__).stem
target_list = list(Path('../repo').resolve(strict=True).glob('*'))
target_list.sort()
for repo_prefix in tqdm(target_list):
    repo_name = repo_prefix.glob('*').__next__().stem
    repo_path = repo_prefix / repo_name
    repo = Repo(repo_path)

    commit_hashes = repo.get_commit_hashes(until=deadline)
    commit_messages = repo.get_commit_messages(until=deadline)

    commit_dict = {commit_hash: commit_message
                   for commit_hash, commit_message in
                   zip(commit_hashes, commit_messages)}

    result_dir = Path(f'../result/{this_file_name}/{repo_name}')
    result_dir.mkdir(exist_ok=True, parents=True)
    result_file_path = result_dir / f'{repo_name}.json'

    with result_file_path.open('w') as f:
        json.dump(commit_dict, f, indent=4)
        f.write('\n')

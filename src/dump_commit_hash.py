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
    result_dir = Path(f'../result/{this_file_name}')
    result_dir.mkdir(exist_ok=True)
    result_file_path = result_dir / f'{repo_name}.json'
    with result_file_path.open('w', encoding='utf-8-sig') as f:
        json.dump(commit_hashes, f, indent=4)

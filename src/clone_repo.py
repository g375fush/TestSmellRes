"""
リポジトリをすべてクローンする．
"""
import os
from pathlib import Path
from subprocess import run

import git


with open('../url_list/dataset_primary.txt', encoding='utf-8') as f:
    url_list = f.read().splitlines()


for index, url in enumerate(url_list, start=1):
    repo_name = url.rsplit('/')[-1].replace('.git', '')
    clone_name = f'[{index:04d}]' + repo_name
    clone_path = Path(f'../repo/[{index:04d}]/{clone_name}').resolve()

    if clone_path.exists():
        print(f'deleting {clone_name} ...')
        repo_prefix = clone_path.parent
        if os.name == 'nt':
            run(['rmdir', '/S', '/Q', str(repo_prefix)], shell=True)
        else:
            run(['rm', '-rf', repo_prefix.as_posix()])
        print(f'deleted {clone_name} !!!')

    print(f'Cloning {clone_name} ...')
    try:
        git.Repo.clone_from(url=url, to_path=clone_path)
    except git.GitCommandError as e:
        print(f'failed to clone {clone_name} ...')
        print(f'due to: {e.stderr}')
        continue
    print(f'Cloned {clone_name} !!!')

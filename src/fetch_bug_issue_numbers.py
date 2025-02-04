"""
GitHub Rest Api を用いてリポジトリの issues を取得し，
そこからバグに関する issue の番号を取得する，
"""
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from tqdm import tqdm

from repo import Repo


def main():
    """
    対象のリポジトリごとに issues を取得してバグに関する issue の番号を取得する．
    """
    result_dir = Path('../result') / Path(__file__).stem
    result_dir.mkdir(exist_ok=True, parents=True)

    token = get_token()
    headers = make_headers(token)

    target_list = [repo_prefix.glob('*').__next__().resolve()
                   for repo_prefix in Path('../repo').glob('*')]
    target_list.sort(key=lambda x: x.name)

    aggregated = {}
    aggregated_file_path = result_dir / 'aggregated.json'
    for target in tqdm(target_list):
        result_file_path = result_dir / target.name / f'{target.name}.json'
        result_file_path.parent.mkdir(exist_ok=True)
        if result_file_path.exists():
            with result_file_path.open() as f:
                aggregated[target.name] = json.load(f)
            continue

        api_url = make_api_url(Repo(target))
        issues = fetch_issues(api_url, headers)

        bug_labels = get_bug_labels(target.name)

        bug_issue_numbers = get_bug_issue_numbers(issues, bug_labels)

        with result_file_path.open('w') as f:
            json.dump(bug_issue_numbers, f, indent=4)

        aggregated[target.name] = bug_issue_numbers

    with aggregated_file_path.open('w') as f:
        json.dump(aggregated, f, indent=4)


def get_token() -> str:
    """
    .env 内のアクセストークンを取得する
    :return: アクセストークン
    """
    load_dotenv()
    return os.getenv("TOKEN")


def make_headers(token) -> dict:
    """
    ヘッダーにトークンを埋め込む．
    :param token: アクセストークン．
    :return: ヘッダー
    """
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    return headers


def make_api_url(repo: Repo) -> str:
    """
    リポジトリの url から api 用の url を作成する．
    :return:
    """
    clone_url = repo.get_clone_url()
    api_url = clone_url.replace('github.com', 'api.github.com/repos')[:-4]
    return api_url


def fetch_issues(api_url: str, headers: dict) -> list:
    """
    issue をすべて取得する．
    :param api_url: リポジトリごとの情報にアクセスするための url．
    :param headers: 認証情報を含んでいるヘッダー．
    :return: issue のリスト．
    """
    issues = []
    api_url += f'/issues?state=all&per_page=100&page=1'
    while api_url:
        response = requests.get(api_url, headers=headers)
        api_url = response.links.get('next', {}).get('url', '')
        issues.extend(response.json())
    return issues


def get_bug_labels(repo_name: str) -> list:
    """
    事前に取得したバグに関するラベルを読み込む．
    :param repo_name: リポジトリの名前．結果を格納するファイル名などの識別に使用する．
    :return: バグに関連するラベル．
    """
    file_path = Path(f'../result/fetch_bug_labels/{repo_name}/{repo_name}.json')
    with file_path.open() as f:
        return json.load(f)


def get_bug_issue_numbers(issues: list, bug_labels: list) -> list:
    """
    取得した issues から，バグに関連する issue を取得し，その数値をひとまとめにする．
    :param issues: すべての issue．
    :param bug_labels: バグに関連するラベル．
    :return: バグに関するラベルが付与された issue の番号のリスト．
    """
    bug_issue_numbers = set()
    for issue in tqdm(issues, leave=False):
        for label in issue['labels']:
            if label['name'] in bug_labels:
                bug_issue_numbers.add(issue['number'])
    return sorted(list(bug_issue_numbers))


if __name__ == '__main__':
    main()

"""
bug labels を GitHub Rest Api を用いて取得し，
ユーザーにその一覧を表示させる．
ユーザーが，ラベルを選択するとそれを結果に書き込むプログラム．
"""
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from repo import Repo


def main():
    """
    bug labels を GitHub Rest Api を用いて取得し，
    ユーザーにその一覧を表示させる．
    ユーザーが，ラベルを選択するとそれを結果に書き込む．
    """
    result_dir = Path('../result') / Path(__file__).stem
    result_dir.mkdir(exist_ok=True, parents=True)

    token = get_token()
    header = make_header(token)

    target_list = [repo_prefix.glob('*').__next__().resolve()
                   for repo_prefix in Path('../repo').glob('*')]
    for target in target_list:
        result_file_path = result_dir / target.name / f'{target.name}.json'
        result_file_path.parent.mkdir(exist_ok=True)
        if result_file_path.exists():
            continue
        api_url = make_api_url(Repo(target))
        labels = fetch_labels(api_url, header)
        bug_labels = decide_labels(labels)

        with result_file_path.open('w') as f:
            json.dump(bug_labels, f)


def get_token() -> str:
    """
    .env 内のアクセストークンを取得する
    :return: アクセストークン
    """
    load_dotenv()
    return os.getenv("TOKEN")


def make_header(token) -> dict:
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


def fetch_labels(api_url: str, header: dict) -> list:
    """
    api 経由で全てのラベルを取得する．
    """
    labels = []
    api_url += f'/labels?per_page=100'
    while api_url:
        response = requests.get(api_url, headers=header)
        if response.status_code == 404:
            return []
        labels.extend(response.json())
        api_url = response.links.get('next', {}).get('url', '')
    return labels


def decide_labels(labels: list):
    """
    GitHub REST APIから得られるissueのラベル情報リストを元に．
    ラベルの選択肢を表示し，ユーザーが選択したラベルのnameをリストで返す．
    複数選択可能で，空入力の場合は空リストを返す．
    """
    show_options(labels)

    user_input = input('バグに関連していると思われるラベルを選択してください：')
    if not user_input.strip():
        return []

    choices = [int(x) for x in user_input.split()]
    return [labels[c - 1]['name'] for c in sorted(choices)]


def show_options(labels: list):
    """
    ラベルを番号付きで表示する.
     nameを選択肢、descriptionを補助情報として表示する.
     """
    if not labels:
        print('no labels!')
        return
    max_len = max(len(label['name']) for label in labels)
    for i, label in enumerate(labels, 1):
        name = label['name']
        desc = label['description'] if label['description'] else ""
        print(f'{i:>3}: {name:<{max_len + 1}}: {desc}')


if __name__ == '__main__':
    main()

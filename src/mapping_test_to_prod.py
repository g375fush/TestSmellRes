"""
unittest を読み込んでいる .py ファイルを読み込み，製品コードとの対応付けを行う．
対応付けには，モジュールのインポート形式とパスとの間の関係を使用する．
候補が 2 以上存在する場合は断定できないため対応付けをしない．
"""
import ast
import json
import sys
from ast import NodeVisitor
from pathlib import Path

from tqdm import tqdm

from repo import Repo
from global_var import deadline


def main():
    """
    解析するリポジトリを決定し，
    リポジトリの各コミットごとに対応付けを行う．
    """
    sys.setrecursionlimit(10000)  # ast 解析中の再帰制限対策

    start = input('start:').zfill(4)
    end = input('end:').zfill(4)

    this_file_name = Path(__file__).stem
    result_root = Path('../result').resolve() / this_file_name
    result_root.mkdir(exist_ok=True, parents=True)

    repo_prefixes = Path('../repo').resolve(strict=True).glob('*')
    target_list = [repo_prefix.glob('*').__next__()
                   for repo_prefix in repo_prefixes
                   if start <= repo_prefix.name[1:5] <= end]
    target_list.sort()

    repo_list = [Repo(target) for target in target_list]
    mapping_per_repo(result_root, repo_list)


def mapping_per_repo(result_root: Path, repo_list: list[Repo]):
    """
    リポジトリごとに対応付けを行う．
    """
    for repo in tqdm(repo_list):
        result_dir = result_root / repo.name
        mapping_per_commit(repo, result_dir)


def mapping_per_commit(repo: Repo, result_dir: Path):
    """
    コミットごとに対応付けを行う．
    :param repo: リポジトリを操作するクラス．
    :param result_dir: 結果を格納するディレクトリ．
    """
    result_dir.mkdir(exist_ok=True)
    commit_hashes = repo.get_commit_hashes(until=deadline)
    for i, commit_hash in enumerate(tqdm(commit_hashes, leave=False), start=1):
        result_file = f'{repo.name}_{i:06d}_{commit_hash}.json'
        result_path = result_dir / result_file
        if result_path.exists():
            continue
        repo.checkout(commit_hash)
        result = mapping_per_file(repo)
        with result_path.open('w', encoding='utf-8') as f:
            json.dump(result, f, indent=4)


def mapping_per_file(repo: Repo) -> dict:
    """
    ファイルごとに対応付けを行う．
    :param repo: リポジトリを操作するクラス．
    """
    result = {}
    python_files = list(repo.repo_path.rglob('*.py'))
    for python_file in tqdm(python_files, leave=False):
        files = mapping(repo, python_file)
        if files:
            result[python_file.relative_to(repo.repo_path).as_posix()] = files
    return result


def mapping(repo: Repo, python_file: Path):
    """
    python_file が unittest を インポートしていればテストファイルとみなす．
    python_file がインポートしているファイルをパスから特定する．
    候補が 2 つから絞れない場合は見つからなかったことにする．
    :param repo: リポジトリを操作するクラス．検索用．
    :param python_file: マッピング対象のファイル．
    """
    try:
        modules = get_imports(python_file)
    except SyntaxError:
        return None
    except UnicodeDecodeError:
        return None
    except FileNotFoundError:  # シンボリックリンクの可能性がある．
        return None
    except IsADirectoryError:  # .pyがついたディレクトリの可能性がある．
        return None
    except ValueError:  # null byte が含まれている可能性がある．
        return None

    if not import_unittest(modules):
        return None

    result = []
    for module in modules:
        module_like_path = Path(module.replace('.', '/')).with_suffix('.py')

        while True:
            hits = list(repo.repo_path.rglob(module_like_path.as_posix()))
            if hits:
                if len(hits) == 1:
                    hit_path = hits[0].relative_to(repo.repo_path).as_posix()
                    result.append(hit_path)
                break
            elif module_like_path.parent.as_posix() == '.':
                break
            else:
                module_like_path = module_like_path.parent.with_suffix('.py')

    return result


def get_imports(file: Path) -> list[str]:
    """
    ast 解析でインポートしているモジュールを抽出する．
    """
    with file.open(encoding='utf-8') as f:
        contents = f.read()

    class ImportVisitor(NodeVisitor):
        """
        コード内の import, from import 文を集めるクラス．
        """
        def __init__(self):
            self.modules = []

        def visit_ImportFrom(self, node):
            """
            from import 文を集める．
            """
            for alias in node.names:
                if node.module is None:
                    self.modules.append(alias.name)
                elif alias.name == '*':
                    self.modules.append(node.module)
                else:
                    self.modules.append(node.module + '.' + alias.name)

        def visit_Import(self, node):
            """
            import 文を集める．
            """
            for alias in node.names:
                self.modules.append(alias.name)

    visitor = ImportVisitor()
    visitor.visit(ast.parse(contents))
    modules = visitor.modules
    return modules


def import_unittest(modules) -> bool:
    """
    unittest を import しているかを確認する．
    """
    for module in modules:
        if 'unittest' in module:
            return True
    return False


if __name__ == '__main__':
    main()

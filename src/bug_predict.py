"""
ランダムフォレストを使用してバグ予測を行う．
テストスメルのデータ，製品コードの 20 種類のメトリクス，
テストコードの 20 種類のメトリクスの順で予測を行う．
"""

import json
from matplotlib import pyplot as plt
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_curve, auc
from sklearn.model_selection import StratifiedKFold


def shuffle_data(X, y, seed=42): # noqa
    """
    X と y の対応を保ったままシャッフルする．
    """
    np.random.seed(seed)
    indices = np.random.permutation(len(X))
    X_shuffled = np.array(X)[indices] # noqa
    y_shuffled = np.array(y)[indices]
    return X_shuffled, y_shuffled


def main():
    """
    テストスメルのデータ，製品コードの 20 種類のメトリクス，
    テストコードの 20 種類のメトリクスの順で予測を行う．
    ROC を適応して， AUC を算出し，10 分割の交差検証を実施する．
    """
    with Path(f'../result/data_forge/aggregated.json').open() as f:
        data_for_prediction = json.load(f)
    predict_using_test_smell(data_for_prediction)
    predict_using_prod_metrics(data_for_prediction)
    predict_using_test_metrics(data_for_prediction)


def predict_using_test_smell(data_for_prediction: dict):
    """
    テストスメルの情報でバグ予測を行う．
    """
    feature_names, X = get_smell_data(data_for_prediction) # noqa
    y = get_bug_data(data_for_prediction)
    X, y = shuffle_data(X, y) # noqa
    model = RandomForestClassifier(random_state=42)
    mean_fpr, mean_tpr, mean_auc, std_auc = predict(model, X, y)
    plot_roc_curve(mean_fpr, mean_tpr, mean_auc, std_auc)


def predict_using_prod_metrics(data_for_prediction: dict):
    """
    製品コードのメトリクスの情報でバグ予測を行う．
    """
    feature_names, X = get_prod_metrics_data(data_for_prediction) # noqa
    y = get_bug_data(data_for_prediction)
    X, y = shuffle_data(X, y) # noqa
    model = RandomForestClassifier(random_state=42)
    mean_fpr, mean_tpr, mean_auc, std_auc = predict(model, X, y)
    plot_roc_curve(mean_fpr, mean_tpr, mean_auc, std_auc)


def predict_using_test_metrics(data_for_prediction: dict):
    """
    テストコードのメトリクスの情報でバグ予測を行う．
    """
    feature_names, X = get_test_metrics_data(data_for_prediction) # noqa
    y = get_bug_data(data_for_prediction)
    X, y = shuffle_data(X, y) # noqa
    model = RandomForestClassifier(random_state=42)
    mean_fpr, mean_tpr, mean_auc, std_auc = predict(model, X, y)
    plot_roc_curve(mean_fpr, mean_tpr, mean_auc, std_auc)


def get_bug_data(data_for_prediction) -> list:
    """
    バグかどうかを表す数値を取得する．
    """
    bug_data = []
    for url, files in data_for_prediction.items():
        for file_path, metrics in files.items():
            bug_data.append(metrics['bug'])
    return bug_data


def get_smell_data(data_for_prediction) -> tuple[list, list[list]]:
    """
    テストスメルのデータを取得する．
    """
    smell_names = []
    smell_data = []
    for url, files in data_for_prediction.items():
        for file_path, metrics in files.items():
            smell_data.append(list(metrics['pynose_result'].values()))
            if not smell_names:
                smell_names = list(metrics['pynose_result'].keys())
    return smell_names, smell_data


def get_prod_metrics_data(data_for_prediction) -> tuple[list, list[list]]:
    """
    製品コードのメトリクスデータを取得する．
    """
    metrics_name = []
    metrics_data = []
    for url, files in data_for_prediction.items():
        for file_path, metrics in files.items():
            metrics_data.append(list(metrics['prod_metrics'].values()))
            if not metrics_name:
                metrics_name = list(metrics['prod_metrics'].keys())
    return metrics_name, metrics_data


def get_test_metrics_data(data_for_prediction) -> tuple[list, list[list]]:
    """
    テストコードのメトリクスデータを取得する．
    """
    metrics_name = []
    metrics_data = []
    for url, files in data_for_prediction.items():
        for file_path, metrics in files.items():
            metrics_data.append(list(metrics['test_metrics'].values()))
            if not metrics_name:
                metrics_name = list(metrics['test_metrics'].keys())
    return metrics_name, metrics_data


def predict(model, X, y): # noqa
    """
    与えられたモデルに対してROC曲線をプロットし，AUCを計算する．
    """
    cv = StratifiedKFold(n_splits=10)
    tprs = []
    aucs = []
    mean_fpr = np.linspace(0, 1, 100)

    for train, test in cv.split(X, y):
        model.fit(X[train], y[train])
        y_proba = model.predict_proba(X[test])[:, 1]
        fpr, tpr, _ = roc_curve(y[test], y_proba)

        tpr_interp = np.interp(mean_fpr, fpr, tpr)
        tpr_interp[0] = 0.0
        tprs.append(tpr_interp)
        roc_auc = auc(fpr, tpr)
        aucs.append(roc_auc)

    mean_tpr = np.mean(tprs, axis=0)
    mean_tpr[-1] = 1.0
    mean_auc = auc(mean_fpr, mean_tpr)
    std_auc = np.std(aucs)

    return mean_fpr, mean_tpr, mean_auc, std_auc


def plot_roc_curve(mean_fpr, mean_tpr, mean_auc, std_auc):
    """
    計算済みのROC曲線データを用いてプロットを行う．
    :param mean_fpr: 平均False Positive Rate (numpy array)
    :param mean_tpr: 平均True Positive Rate (numpy array)
    :param mean_auc: 平均AUC値 (float)
    :param std_auc: AUC値の標準偏差 (float)
    """
    plt.plot([0, 1], [0, 1], linestyle='--', lw=2, color='k', alpha=.8)
    plt.plot(mean_fpr, mean_tpr, linestyle='-', lw=2, color='k',
             label=r'Mean ROC (AUC = %0.2f $\pm$ %0.2f)' % (mean_auc, std_auc))
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=14)
    plt.ylabel('True Positive Rate', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(loc="lower right")
    plt.show()


if __name__ == '__main__':
    main()

"""Run the full reproducible USPS / Sonar assignment. No GPU required."""
import argparse
import csv
import hashlib
import json
import platform
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import scipy
import sklearn
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.model_selection import StratifiedKFold, train_test_split
from threadpoolctl import threadpool_limits
from models import Fisher, knn_predict_many, preprocess

ROOT = Path(__file__).resolve().parents[1]
KS = [1, 3, 5, 7, 9, 11, 15, 21]
ALPHAS = [0.001, 0.01, 0.1]
METHODS = ['KNN', 'Fisher', 'Fisher+KNN']


def write_csv(name, rows):
    if rows:
        with (ROOT / 'results' / name).open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def load_data():
    train = np.loadtxt(ROOT / 'data/zip.train.gz')
    test = np.loadtxt(ROOT / 'data/zip.test.gz')
    with zipfile.ZipFile(ROOT / 'data/sonar.zip') as z:
        name = next(n for n in z.namelist() if n.endswith('sonar.all-data'))
        sonar = np.loadtxt(z.open(name), delimiter=',', dtype=str)
    Xs = sonar[:, :-1].astype(float)
    ys = (sonar[:, -1] == 'M').astype(int)  # 0=rock, 1=mine
    assert train.shape == (7291, 257) and test.shape == (2007, 257)
    assert Xs.shape == (208, 60) and np.bincount(ys).tolist() == [97, 111]
    for X in [train, test, Xs]:
        assert np.isfinite(X).all()
    return train[:, 1:], train[:, 0].astype(int), test[:, 1:], test[:, 0].astype(int), Xs, ys


def select_parameters(X, y, dataset, seed=42, folds=5):
    """Each fold refits preprocessing and Fisher using only its training part."""
    cv = StratifiedKFold(folds, shuffle=True, random_state=seed)
    scores = {(m, a, k): [] for m in METHODS
              for a in ([0.0] if m == 'KNN' else ALPHAS)
              for k in ([0] if m == 'Fisher' else KS)}
    for train_idx, val_idx in cv.split(X, y):
        Xt, Xv = preprocess(X[train_idx], X[val_idx], dataset)
        yt, yv = y[train_idx], y[val_idx]
        for k, pred in knn_predict_many(Xt, yt, Xv, KS).items():
            scores['KNN', 0.0, k].append(accuracy_score(yv, pred))
        for alpha in ALPHAS:
            fisher = Fisher(alpha).fit(Xt, yt)
            scores['Fisher', alpha, 0].append(accuracy_score(yv, fisher.predict(Xv)))
            for k, pred in knn_predict_many(fisher.transform(Xt), yt,
                                           fisher.transform(Xv), KS).items():
                scores['Fisher+KNN', alpha, k].append(accuracy_score(yv, pred))
    rows = [dict(dataset=dataset, method=m, alpha=a, k=k,
                 cv_mean=float(np.mean(values)), cv_std=float(np.std(values, ddof=1)))
            for (m, a, k), values in scores.items()]
    selected = {}
    for method in METHODS:
        # Equal mean: prefer stronger regularization, then smaller K.
        best = sorted([r for r in rows if r['method'] == method],
                      key=lambda r: (-r['cv_mean'], -r['alpha'], r['k']))[0]
        selected[method] = dict(alpha=best['alpha'], k=best['k'], cv_mean=best['cv_mean'])
    return selected, rows


def evaluate(Xt, yt, Xe, ye, dataset, params, all_k=False):
    Xt, Xe = preprocess(Xt, Xe, dataset)
    predictions, models, result = {}, {}, []
    for method in METHODS:
        start = time.perf_counter()
        par = params[method]
        if method == 'KNN':
            Zt, Ze = Xt, Xe
            model = None
        else:
            model = Fisher(par['alpha']).fit(Xt, yt)
            Zt, Ze = model.transform(Xt), model.transform(Xe)
        fit_s = time.perf_counter() - start
        start = time.perf_counter()
        if method == 'Fisher':
            pred_map = {0: model.predict(Xe)}
        else:
            pred_map = knn_predict_many(Zt, yt, Ze, KS if all_k else [par['k']])
        predict_s = time.perf_counter() - start
        for k, pred in pred_map.items():
            result.append(dict(dataset=dataset, method=method, k=k, alpha=par['alpha'],
                               n_train=len(yt), n_test=len(ye),
                               accuracy=float(accuracy_score(ye, pred)),
                               error=float(1 - accuracy_score(ye, pred)),
                               macro_f1=float(f1_score(ye, pred, average='macro')),
                               fit_seconds=fit_s, predict_seconds=predict_s))
        predictions[method] = pred_map[par['k']]
        models[method] = model
    return result, predictions, models


def nested_subset(y, fraction, seed):
    """Per-class shuffled prefixes: larger fractions contain smaller subsets."""
    rng = np.random.default_rng(seed)
    selected = []
    for c in np.unique(y):
        indices = rng.permutation(np.flatnonzero(y == c))
        selected.extend(indices[:max(1, int(np.floor(fraction * len(indices))))])
    return np.sort(selected)


def aggregate(rows, keys, metrics=('accuracy', 'error', 'macro_f1')):
    groups = {}
    for row in rows:
        groups.setdefault(tuple(row[k] for k in keys), []).append(row)
    out = []
    for group, records in groups.items():
        row = dict(zip(keys, group))
        row['repeats'] = len(records)
        for metric in metrics:
            vals = [r[metric] for r in records]
            row[metric + '_mean'] = float(np.mean(vals))
            row[metric + '_std'] = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
        out.append(row)
    return out


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sonar-repeats', type=int, default=20)
    parser.add_argument('--usps-repeats', type=int, default=5)
    args = parser.parse_args()
    start = time.perf_counter()
    (ROOT / 'results').mkdir(exist_ok=True)
    X, y, Xe, ye, Xs, ys = load_data()
    settings = dict(ks=KS, alphas=ALPHAS, main_seed=42, cv_folds=5,
                    sonar_repeats=args.sonar_repeats, usps_repeats=args.usps_repeats,
                    python=sys.version, numpy=np.__version__, scipy=scipy.__version__,
                    sklearn=sklearn.__version__, platform=platform.platform(),
                    protocol='USPS official test; Sonar repeated stratified holdouts; inner CV only')
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((ROOT / 'data').iterdir()) if p.is_file()}
    settings['data_sha256'] = hashes
    (ROOT / 'results/settings.json').write_text(json.dumps(settings, indent=2), encoding='utf-8')
    cvs, mains, details, learning = [], [], {}, []
    fixed = {'KNN': dict(k=3, alpha=0.0), 'Fisher': dict(k=0, alpha=0.01),
             'Fisher+KNN': dict(k=3, alpha=0.01)}
    all_splits = {}
    print('USPS: selecting hyperparameters with 5-fold training-only CV', flush=True)
    params, rows = select_parameters(X, y, 'USPS')
    cvs.extend(rows)
    result, preds, _ = evaluate(X, y, Xe, ye, 'USPS', params)
    mains.extend(result)
    details['USPS'] = dict(parameters=params, confusion={m: confusion_matrix(ye, p).tolist()
                                                       for m, p in preds.items()})
    np.savez_compressed(ROOT / 'results/usps_predictions.npz', y_true=ye,
                        **{m.replace('+', '_'): p for m, p in preds.items()})
    print('USPS main:', result, flush=True)
    for seed in range(args.usps_repeats):
        for fraction in [0.2, 0.4, 0.6, 0.8, 1.0]:
            idx = nested_subset(y, fraction, seed)
            all_splits[f'usps_{seed}_{fraction}_train'] = idx
            result, _, _ = evaluate(X[idx], y[idx], Xe, ye, 'USPS', fixed)
            learning.extend([dict(**r, seed=seed, fraction=fraction) for r in result])
        print(f'USPS learning curve: repeat {seed + 1}/{args.usps_repeats}', flush=True)
    # Sonar main report uses seed 42. Repetitions use seeds 42..61 by default.
    repeated, k_sweep = [], []
    for seed in range(42, 42 + args.sonar_repeats):
        tr, te = train_test_split(np.arange(len(ys)), test_size=0.2,
                                 stratify=ys, random_state=seed)
        all_splits[f'sonar_{seed}_train'] = tr
        all_splits[f'sonar_{seed}_test'] = te
        params, rows = select_parameters(Xs[tr], ys[tr], 'Sonar', seed)
        result, preds, _ = evaluate(Xs[tr], ys[tr], Xs[te], ys[te], 'Sonar', params)
        repeated.extend([dict(**r, seed=seed) for r in result])
        if seed == 42:
            cvs.extend(rows)
            mains.extend(result)
            details['Sonar'] = dict(parameters=params, confusion={m: confusion_matrix(ys[te], p).tolist()
                                                                for m, p in preds.items()})
            np.savez_compressed(ROOT / 'results/sonar_predictions.npz', test_indices=te,
                                y_true=ys[te], **{m.replace('+', '_'): p for m, p in preds.items()})
        for fraction in [0.2, 0.4, 0.6, 0.8, 1.0]:
            idx = nested_subset(ys[tr], fraction, seed)
            result, _, _ = evaluate(Xs[tr][idx], ys[tr][idx], Xs[te], ys[te], 'Sonar', fixed)
            learning.extend([dict(**r, seed=seed, fraction=fraction) for r in result])
        # K sensitivity uses fixed alpha and reports descriptive test curves;
        # it is never used to select the main-report K.
        result, _, _ = evaluate(Xs[tr], ys[tr], Xs[te], ys[te], 'Sonar', fixed, all_k=True)
        k_sweep.extend([dict(**r, seed=seed) for r in result])
        print(f'Sonar nested evaluation: repeat {seed - 41}/{args.sonar_repeats}', flush=True)
    result, _, _ = evaluate(X, y, Xe, ye, 'USPS', fixed, all_k=True)
    k_sweep.extend([dict(**r, seed=42) for r in result])
    # Literal train/test-ratio study complements the fixed-test learning curves.
    ratios = []
    for seed in range(42, 42 + args.sonar_repeats):
        for ratio in [0.2, 0.4, 0.6, 0.8]:
            tr, te = train_test_split(np.arange(len(ys)), train_size=ratio,
                                     stratify=ys, random_state=seed)
            all_splits[f'ratio_{seed}_{ratio}_train'] = tr
            all_splits[f'ratio_{seed}_{ratio}_test'] = te
            result, _, _ = evaluate(Xs[tr], ys[tr], Xs[te], ys[te], 'Sonar', fixed)
            ratios.extend([dict(**r, seed=seed, train_ratio=ratio) for r in result])
    write_csv('main_results.csv', mains)
    write_csv('cv_results.csv', cvs)
    write_csv('sonar_repeated.csv', repeated)
    write_csv('sonar_summary.csv', aggregate(repeated, ['dataset', 'method']))
    write_csv('learning_raw.csv', learning)
    write_csv('learning_summary.csv', aggregate(learning, ['dataset', 'method', 'fraction', 'n_train', 'n_test']))
    write_csv('k_sweep_raw.csv', k_sweep)
    write_csv('k_sweep_summary.csv', aggregate(k_sweep, ['dataset', 'method', 'k']))
    write_csv('ratio_raw.csv', ratios)
    write_csv('ratio_summary.csv', aggregate(ratios, ['dataset', 'method', 'train_ratio', 'n_train', 'n_test']))
    np.savez_compressed(ROOT / 'results/split_indices.npz', **all_splits)
    details['elapsed_seconds'] = time.perf_counter() - start
    (ROOT / 'results/details.json').write_text(json.dumps(details, indent=2), encoding='utf-8')
    print('DONE in %.1f seconds' % details['elapsed_seconds'], flush=True)


if __name__ == '__main__':
    with threadpool_limits(limits=2):
        run()

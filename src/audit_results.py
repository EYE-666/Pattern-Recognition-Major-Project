"""Validate saved results, partitions, data integrity and report facts."""
import csv
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from experiment import load_data, METHODS

ROOT=Path(__file__).resolve().parents[1]


def main():
    X,y,T,t,S,s=load_data()
    splits=np.load(ROOT/'results/split_indices.npz')
    for seed in range(42,62):
        tr,te=splits[f'sonar_{seed}_train'],splits[f'sonar_{seed}_test']
        assert len(set(tr)&set(te))==0
        assert sorted(np.r_[tr,te])==list(range(208))
        for ratio in [.2,.4,.6,.8]:
            a,b=splits[f'ratio_{seed}_{ratio}_train'],splits[f'ratio_{seed}_{ratio}_test']
            assert not set(a)&set(b)
            assert sorted(np.r_[a,b])==list(range(208))
    for seed in range(5):
        prev=set()
        for f in [.2,.4,.6,.8,1.]:
            curr=set(splits[f'usps_{seed}_{f}_train'])
            assert prev <= curr
            prev=curr
    with (ROOT/'results/main_results.csv').open(encoding='utf-8-sig') as f:
        main_rows=list(csv.DictReader(f))
    for dataset in ['USPS','Sonar']:
        pred=np.load(ROOT/f'results/{dataset.lower()}_predictions.npz')
        for m in METHODS:
            r=next(r for r in main_rows if r['dataset']==dataset and r['method']==m)
            p=pred[m.replace('+','_')]
            assert np.isclose(accuracy_score(pred['y_true'],p),float(r['accuracy']))
            assert np.isclose(f1_score(pred['y_true'],p,average='macro'),float(r['macro_f1']))
    for path in (ROOT/'results').glob('*.csv'):
        with path.open(encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                for metric in ['accuracy','error','macro_f1','cv_mean','accuracy_mean','error_mean']:
                    if metric in r:
                        assert 0 <= float(r[metric]) <= 1
                if 'accuracy' in r:
                    assert np.isclose(float(r['accuracy'])+float(r['error']),1)
    facts=dict(usps_train_counts=np.bincount(y).tolist(),usps_test_counts=np.bincount(t).tolist(),
               usps_train_shape=list(X.shape),usps_test_shape=list(T.shape),sonar_shape=list(S.shape),
               sonar_class_counts=np.bincount(s).tolist(),
               usps_duplicate_rows=len(X)+len(T)-len(np.unique(np.vstack([X,T]),axis=0)),
               sonar_duplicate_rows=len(S)-len(np.unique(S,axis=0)),
               all_finite=bool(all(np.isfinite(a).all() for a in [X,T,S])),
               checks='PASS: disjoint partitions; nested subsets; metrics recomputed; bounds; duplicates')
    (ROOT/'results/audit.json').write_text(json.dumps(facts,indent=2),encoding='utf-8')
    print(facts['checks'])


if __name__=='__main__':
    main()

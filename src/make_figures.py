"""Generate publication-style figures from actual saved experiment outputs."""
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from models import Fisher, preprocess
from experiment import load_data, METHODS

ROOT = Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family': 'Microsoft YaHei', 'font.size': 10,
                     'axes.unicode_minus': False, 'figure.dpi': 140,
                     'savefig.dpi': 200, 'axes.spines.top': False,
                     'axes.spines.right': False})
COLORS = {'KNN': '#2367A0', 'Fisher': '#CA7138', 'Fisher+KNN': '#238877'}


def rows(name):
    with (ROOT / 'results' / name).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def save(fig, name):
    fig.savefig(ROOT / 'figures' / name, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def main():
    X, y, Xe, ye, Xs, ys = load_data()
    details = json.loads((ROOT / 'results/details.json').read_text())
    # Actual training images, two samples per digit.
    fig, axes = plt.subplots(2, 10, figsize=(10, 2.7))
    for c in range(10):
        for r in range(2):
            axes[r, c].imshow(X[np.flatnonzero(y == c)[r]].reshape(16, 16),
                              cmap='gray', vmin=-1, vmax=1)
            axes[r, c].axis('off')
            if r == 0:
                axes[r, c].set_title(str(c))
    fig.tight_layout()
    save(fig, '01_usps_samples.png')
    # Fixed-alpha K sensitivity, means and standard deviations for Sonar.
    kr = rows('k_sweep_summary.csv')
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7))
    for ax, dataset in zip(axes, ['USPS', 'Sonar']):
        for m in METHODS:
            subset = [r for r in kr if r['dataset'] == dataset and r['method'] == m]
            if m == 'Fisher':
                ax.axhline(100*float(subset[0]['accuracy_mean']), linestyle='--',
                           color=COLORS[m], label='Fisher（不依赖 K）')
            else:
                subset.sort(key=lambda r: int(r['k']))
                kvals = [int(r['k']) for r in subset]
                mean = 100*np.array([float(r['accuracy_mean']) for r in subset])
                std = 100*np.array([float(r['accuracy_std']) for r in subset])
                ax.plot(kvals, mean, 'o-', label=m, color=COLORS[m], markersize=4)
                if dataset == 'Sonar':
                    ax.fill_between(kvals, mean-std, mean+std, color=COLORS[m], alpha=.12)
        ax.set(title=dataset, xlabel='邻居数 K', ylabel='测试正确率 / %', xticks=[1,5,9,15,21])
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, '02_k_accuracy.png')
    # Error is explicitly shown as requested by assignment.
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.3))
    for ax, dataset in zip(axes, ['USPS', 'Sonar']):
        for m in ['KNN', 'Fisher+KNN']:
            ss = sorted([r for r in kr if r['dataset']==dataset and r['method']==m],key=lambda r:int(r['k']))
            ax.plot([int(r['k']) for r in ss], [100*float(r['error_mean']) for r in ss],
                    'o-', color=COLORS[m],label=m,markersize=4)
        ax.set(title=dataset, xlabel='邻居数 K', ylabel='测试错误率 / %')
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, '03_k_error.png')
    lr = rows('learning_summary.csv')
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7))
    for ax, dataset in zip(axes, ['USPS', 'Sonar']):
        for m in METHODS:
            ss = sorted([r for r in lr if r['dataset']==dataset and r['method']==m],key=lambda r:float(r['fraction']))
            frac = [100*float(r['fraction']) for r in ss]
            mean = 100*np.array([float(r['accuracy_mean']) for r in ss])
            std = 100*np.array([float(r['accuracy_std']) for r in ss])
            ax.plot(frac,mean,'o-',label=m,color=COLORS[m],markersize=4)
            ax.fill_between(frac,mean-std,mean+std,alpha=.12,color=COLORS[m])
        ax.set(title=dataset,xlabel='使用训练池的比例 / %',ylabel='测试正确率 / %',xticks=[20,40,60,80,100])
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, '04_learning_curve.png')
    rr = rows('ratio_summary.csv')
    fig, ax = plt.subplots(figsize=(8.3,3.4))
    for m in METHODS:
        ss = sorted([r for r in rr if r['method']==m],key=lambda r:float(r['train_ratio']))
        xx = [100*float(r['train_ratio']) for r in ss]
        mean = 100*np.array([float(r['accuracy_mean']) for r in ss])
        std = 100*np.array([float(r['accuracy_std']) for r in ss])
        ax.errorbar(xx,mean,yerr=std,fmt='o-',capsize=4,label=m,color=COLORS[m])
    ax.set(xlabel='训练集占全部 Sonar 样本的比例 / %',ylabel='测试正确率 / %',xticks=[20,40,60,80])
    ax.legend(ncol=3,fontsize=9)
    ax.grid(alpha=.2)
    fig.tight_layout()
    save(fig, '05_ratio_curve.png')
    # Confusion matrices of all methods; Sonar explicitly labels rock/mine.
    for dataset in ['USPS','Sonar']:
        fig, axes = plt.subplots(1,3,figsize=(10,3.5 if dataset=='USPS' else 3.1))
        for ax,m in zip(axes,METHODS):
            cm=np.array(details[dataset]['confusion'][m])
            im=ax.imshow(cm,cmap='Blues')
            labels=list(range(10)) if dataset=='USPS' else ['R 岩石','M 金属']
            ax.set(xticks=range(len(labels)),yticks=range(len(labels)),
                   xticklabels=labels,yticklabels=labels,title=m,xlabel='预测类别',ylabel='真实类别')
            for i in range(len(cm)):
                for j in range(len(cm)):
                    ax.text(j,i,str(cm[i,j]),ha='center',va='center',
                            fontsize=6 if dataset=='USPS' else 13,
                            color='white' if cm[i,j]>cm.max()*.55 else '#222222')
        fig.tight_layout()
        save(fig, f'06_confusion_{dataset.lower()}.png')
    # Two-dimensional USPS display is not the nine-dimensional classifier.
    Xt, Xq=preprocess(X,Xe,'USPS')
    model=Fisher(details['USPS']['parameters']['Fisher+KNN']['alpha']).fit(Xt,y)
    Z=model.transform(Xq)
    tr,te=train_test_split(np.arange(len(ys)),test_size=.2,stratify=ys,random_state=42)
    St,Sq=preprocess(Xs[tr],Xs[te],'Sonar')
    sm=Fisher(details['Sonar']['parameters']['Fisher']['alpha']).fit(St,ys[tr])
    Sz=sm.transform(Sq)[:,0]
    fig,axes=plt.subplots(1,2,figsize=(10,3.6))
    for c in range(10):
        axes[0].scatter(Z[ye==c,0],Z[ye==c,1],s=5,alpha=.6,label=str(c))
    axes[0].legend(ncol=5,fontsize=7,loc='upper right')
    axes[0].set(title='USPS 测试集前两个 Fisher 方向',xlabel='第一判别方向',ylabel='第二判别方向')
    for c,label in [(0,'R 岩石'),(1,'M 金属')]:
        axes[1].hist(Sz[ys[te]==c],bins=10,alpha=.55,label=label)
    axes[1].set(title='Sonar 测试集一维 Fisher 投影',xlabel='判别投影值',ylabel='样本数')
    axes[1].legend(fontsize=9)
    fig.tight_layout()
    save(fig,'07_fisher_projection.png')
    # Errors shown in original test order, rather than hand-picked examples.
    pp=np.load(ROOT/'results/usps_predictions.npz')
    pred=pp['KNN']
    idx=np.flatnonzero(pred!=ye)[:12]
    fig,axes=plt.subplots(2,6,figsize=(9,3.6))
    for ax,i in zip(axes.flat,idx):
        ax.imshow(Xe[i].reshape(16,16),cmap='gray',vmin=-1,vmax=1)
        ax.set_title(f'#{i}  真 {ye[i]} / 判 {pred[i]}',fontsize=9)
        ax.axis('off')
    fig.tight_layout()
    save(fig,'08_usps_errors.png')
    print('Generated 9 verified-data figures')


if __name__=='__main__':
    main()

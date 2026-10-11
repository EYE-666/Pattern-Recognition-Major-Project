"""Fisher discriminant and exact KNN, implemented from their definitions."""
import numpy as np
from scipy.linalg import eigh
from scipy.spatial.distance import cdist


class Fisher:
    """Regularized Fisher projection; nearest centroid uses equal class priors.

    W is normalized in the regularized within-class covariance metric.
    Consequently Euclidean distance in the projected space has a defined scale.
    """
    def __init__(self, alpha=0.01):
        self.alpha = alpha

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        self.classes_ = np.unique(y)
        n, d = X.shape
        self.mean_ = X.mean(axis=0)
        self.means_ = np.array([X[y == c].mean(axis=0)
                                for c in self.classes_])
        Sw = np.zeros((d, d))
        Sb = np.zeros((d, d))
        for c, mu in zip(self.classes_, self.means_):
            Xc = X[y == c] - mu
            Sw += Xc.T @ Xc / n
            delta = mu - self.mean_
            Sb += len(Xc) * np.outer(delta, delta) / n
        scale = np.trace(Sw) / d
        self.within_ = Sw + self.alpha * max(scale, 1e-12) * np.eye(d)
        dim = min(d, len(self.classes_) - 1)
        eigenvalues, vectors = eigh(Sb, self.within_,
                                    subset_by_index=[d - dim, d - 1])
        self.W_ = vectors[:, ::-1]
        self.eigenvalues_ = eigenvalues[::-1]
        self.centroids_ = self.transform(self.means_)
        return self

    def transform(self, X):
        return (X - self.mean_) @ self.W_

    def predict(self, X):
        distances = cdist(self.transform(X), self.centroids_, 'sqeuclidean')
        return self.classes_[distances.argmin(axis=1)]


def knn_predict_many(X_train, y_train, X_query, ks, batch_size=128):
    """One exact distance search for all K values; deterministic tie rules.

    Equal distances retain training-row order. Equal vote counts choose the
    smallest class label. Stable full sorting avoids argpartition boundary ties.
    """
    ks = sorted(set(int(k) for k in ks))
    if not ks or ks[0] < 1 or ks[-1] > len(y_train):
        raise ValueError('K must be between 1 and the training sample count')
    classes, encoded = np.unique(y_train, return_inverse=True)
    predictions = {k: [] for k in ks}
    for start in range(0, len(X_query), batch_size):
        distances = cdist(X_query[start:start + batch_size], X_train,
                          'sqeuclidean')
        indices = np.argsort(distances, axis=1, kind='stable')[:, :ks[-1]]
        neighbor_labels = encoded[indices]
        counts = np.zeros((len(indices), len(classes)), dtype=int)
        for j in range(ks[-1]):
            counts[np.arange(len(indices)), neighbor_labels[:, j]] += 1
            if j + 1 in predictions:
                predictions[j + 1].append(classes[counts.argmax(axis=1)])
    return {k: np.concatenate(v) for k, v in predictions.items()}


def preprocess(X_train, X_query, dataset):
    """USPS pixels already have a common scale; Sonar uses training-only z-score."""
    if dataset == 'USPS':
        return X_train.copy(), X_query.copy()
    mu = X_train.mean(axis=0)
    sigma = X_train.std(axis=0)
    sigma[sigma < 1e-12] = 1.0
    return (X_train - mu) / sigma, (X_query - mu) / sigma

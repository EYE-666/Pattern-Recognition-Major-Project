"""Independent correctness checks for manually implemented algorithms."""
import numpy as np
from numpy.testing import assert_allclose, assert_array_equal
from sklearn.neighbors import KNeighborsClassifier
from models import Fisher, knn_predict_many, preprocess


def main():
    rng = np.random.default_rng(7)
    X = rng.normal(size=(75, 7))
    y = np.repeat([0, 1, 2], 25)
    X += y[:, None] * 0.7
    Q = rng.normal(size=(11, 7))
    preds = knn_predict_many(X, y, Q, [1, 3, 5, 11])
    for k, pred in preds.items():
        ref = KNeighborsClassifier(k, algorithm='brute').fit(X, y).predict(Q)
        assert_array_equal(pred, ref)
    # Check Fisher classifier against the full-space equal-prior LDA formula.
    model = Fisher(0.01).fit(X, y)
    assert model.W_.shape == (7, 2)
    assert_allclose(model.W_.T @ model.within_ @ model.W_, np.eye(2), atol=1e-9)
    inv_mu = np.linalg.solve(model.within_, model.means_.T)
    discriminant = Q @ inv_mu - 0.5 * np.sum(model.means_.T * inv_mu, axis=0)
    assert_array_equal(model.predict(Q), model.classes_[discriminant.argmax(axis=1)])
    # Singular within-class scatter and p >> n remain finite after regularization.
    small = np.repeat(X[:6], 3, axis=1)
    singular = Fisher().fit(small, np.array([0, 0, 0, 1, 1, 1]))
    assert np.isfinite(singular.W_).all()
    # Exact distance and vote ties are deterministic.
    tied = knn_predict_many(np.array([[-1.], [1.]]), np.array([1, 0]),
                            np.array([[0.]]), [1, 2])
    assert tied[1][0] == 1 and tied[2][0] == 0
    A, B = preprocess(np.array([[1., 3.], [3., 3.]]), np.array([[101., 3.]]), 'Sonar')
    assert_allclose(A.mean(axis=0), 0)
    assert_allclose(B, [[99., 0.]])
    print('PASS: KNN reference, Fisher/LDA equivalence, whitening, singularity, ties, preprocessing')


if __name__ == '__main__':
    main()

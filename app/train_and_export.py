"""
Retrain the NanoMedAI models on your own (real) data and export them in the
JSON format nanomedai.html expects.

Usage:
    python train_and_export.py data.csv nanomedai.html nanomedai_real.html

data.csv columns (exact names):
    Material, Size_nm, Shape, Temperature, pH, Salt, Coating, Stability, Reactivity

    Stability  labels: High / Medium / Low
    Reactivity labels: Low / Moderate / High
    (You can use different labels, but the page's colours/text assume these.)

Optional 10th column "Source" (paper / lab / batch id) is used for
group-aware cross-validation, which is strongly recommended for real data.
"""
import json
import re
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold, KFold, cross_val_score

FEATURE_ORDER = ["Material", "Size_nm", "Shape", "Temperature", "pH", "Salt", "Coating"]
CATEGORICAL = ["Material", "Shape", "Coating"]
TARGETS = ["Stability", "Reactivity"]


def export_tree(est):
    t = est.tree_
    v = t.value[:, 0, :]
    v = v / v.sum(axis=1, keepdims=True)  # normalise (older sklearn stores counts)
    return {
        "f": t.feature.tolist(),          # -2 at leaves
        "t": [round(float(x), 6) for x in t.threshold],
        "l": t.children_left.tolist(),    # -1 at leaves
        "r": t.children_right.tolist(),
        "v": [[round(float(p), 5) for p in row] for row in v],
    }


def main(csv_path, html_in, html_out):
    df = pd.read_csv(csv_path).dropna(subset=FEATURE_ORDER + TARGETS)

    # Categorical encoders: alphabetical, index = position in list
    encoders = {c: sorted(df[c].unique().tolist()) for c in CATEGORICAL}
    X = df[FEATURE_ORDER].copy()
    for c in CATEGORICAL:
        X[c] = X[c].map({name: i for i, name in enumerate(encoders[c])})

    # Cross-validation: group by source if available so the score isn't inflated
    if "Source" in df.columns:
        cv, groups = GroupKFold(n_splits=5), df["Source"]
    else:
        cv, groups = KFold(n_splits=5, shuffle=True, random_state=0), None

    forests, targets, importances = {}, {}, {}
    for target in TARGETS:
        y = df[target]
        clf = RandomForestClassifier(
            n_estimators=100, max_depth=8, min_samples_leaf=3,
            class_weight="balanced", random_state=0, n_jobs=-1,
        )
        scores = cross_val_score(clf, X, y, cv=cv, groups=groups, scoring="balanced_accuracy")
        print(f"{target}: CV balanced accuracy = {scores.mean():.3f} ± {scores.std():.3f}")

        clf.fit(X, y)
        targets[target] = clf.classes_.tolist()  # sorted; matches leaf-vector column order
        forests[target] = [export_tree(e) for e in clf.estimators_]
        importances[target] = {
            name: round(float(imp), 4) for name, imp in zip(FEATURE_ORDER, clf.feature_importances_)
        }

    model_data = {
        "feature_order": FEATURE_ORDER,
        "encoders": encoders,
        "ranges": {  # observed ranges in YOUR data; the UI sliders use these
            "size_nm": [round(float(df.Size_nm.min()), 2), round(float(df.Size_nm.max()), 2)],
            "temperature": [round(float(df.Temperature.min()), 2), round(float(df.Temperature.max()), 2)],
            "ph": [round(float(df.pH.min()), 2), round(float(df.pH.max()), 2)],
            "salt": [round(float(df.Salt.min()), 3), round(float(df.Salt.max()), 3)],
        },
        "targets": targets,
        "forests": forests,
        "feature_importance": importances,
    }

    html = open(html_in, encoding="utf-8").read()
    start = html.index("const MODEL_DATA =") + len("const MODEL_DATA =")
    # Robustly find the end of the old JSON object
    _, old_end = json.JSONDecoder().raw_decode(html[start:].lstrip())
    lead = len(html[start:]) - len(html[start:].lstrip())
    old_end += start + lead
    new_html = html[:start] + "\n" + json.dumps(model_data, separators=(",", ":")) + html[old_end:]
    open(html_out, "w", encoding="utf-8").write(new_html)
    print(f"Wrote {html_out}")
    print("Materials:", encoders["Material"])


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])

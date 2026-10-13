"""Shared practice helpers. Use examples/ as notebook working directory."""
import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_NUM_INTEROP_THREADS", "1")
os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).parent
NUM_CLASS = ["tenure_months", "monthly_fee", "support_calls", "last_usage"]
CAT_CLASS = ["contract_type", "region"]
NUM_REG = ["active_users", "active_days", "storage_gb"]
CAT_REG = ["plan", "region"]

def load_customers():
    return pd.read_csv(ROOT / "data/customers.csv")

def load_usage():
    return pd.read_csv(ROOT / "data/service_usage.csv")

def clean_customers(frame):
    """Fixed business constraints, not data-derived thresholds; input stays unchanged."""
    result = frame.copy()
    result.loc[result["monthly_fee"] < 0, "monthly_fee"] = np.nan
    result.loc[~result["last_usage"].between(0, 100), "last_usage"] = np.nan
    return result

def split_task(task="classification"):
    if task not in {"classification", "regression"}:
        raise ValueError("Unknown task")
    frame = clean_customers(load_customers()) if task == "classification" else load_usage()
    numeric, categorical = (NUM_CLASS, CAT_CLASS) if task == "classification" else (NUM_REG, CAT_REG)
    target = "churn" if task == "classification" else "usage_hours"
    X, y = frame[numeric+categorical], frame[target]
    X_dev, X_test, y_dev, y_test = train_test_split(X, y, test_size=0.2, random_state=42,
        stratify=y if task == "classification" else None)
    X_train, X_val, y_train, y_val = train_test_split(X_dev, y_dev, test_size=0.25, random_state=42,
        stratify=y_dev if task == "classification" else None)
    return X_train, X_val, X_test, y_train, y_val, y_test

def preprocessor(task="classification"):
    numeric, categorical = (NUM_CLASS,CAT_CLASS) if task == "classification" else (NUM_REG,CAT_REG)
    num = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    cat = Pipeline([("imputer",SimpleImputer(strategy="most_frequent")),
                    ("encoder",OneHotEncoder(handle_unknown="ignore",sparse_output=False))])
    return ColumnTransformer([("num",num,numeric),("cat",cat,categorical)])

def dense_data(task="classification"):
    X_train, X_val, X_test, y_train, y_val, y_test = split_task(task)
    prep = preprocessor(task)
    train = prep.fit_transform(X_train).astype("float32")
    val = prep.transform(X_val).astype("float32")
    test = prep.transform(X_test).astype("float32")
    return train, val, test, y_train.to_numpy(dtype="float32"), y_val.to_numpy(dtype="float32"), y_test.to_numpy(dtype="float32"), prep

def keras_model(n_features, task="classification", dropout=0):
    import tensorflow as tf
    tf.keras.backend.clear_session()
    tf.keras.utils.set_random_seed(42)
    layers = [tf.keras.layers.Input(shape=(n_features,)), tf.keras.layers.Dense(32,activation="relu")]
    if dropout:
        layers.append(tf.keras.layers.Dropout(dropout))
    layers += [tf.keras.layers.Dense(16,activation="relu"),
               tf.keras.layers.Dense(1,activation="sigmoid" if task=="classification" else "linear")]
    model = tf.keras.Sequential(layers)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.01),
                  loss="binary_crossentropy" if task=="classification" else "mse",
                  metrics=["accuracy"] if task=="classification" else ["mae"])
    return model

def dataset(X, y=None, training=False):
    import tensorflow as tf
    values = (X,y) if y is not None else X
    data = tf.data.Dataset.from_tensor_slices(values)
    if training:
        data = data.shuffle(len(X),seed=42)
    options = tf.data.Options()
    options.threading.private_threadpool_size=1
    options.threading.max_intra_op_parallelism=1
    return data.batch(32).with_options(options)

def fit_dense(model, X, y, X_val, y_val, epochs=12, callbacks=None):
    return model.fit(dataset(X,y,True), validation_data=dataset(X_val,y_val),
                     epochs=epochs, callbacks=callbacks or [], verbose=0)

def dense_predict(model, X):
    return model.predict(dataset(X),verbose=0).ravel()

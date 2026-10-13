"""Author-created solution. Run from examples/. No external data or AI calls."""

# Q01: 자료 불러오기
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from lab import ROOT
df = pd.read_csv(ROOT / 'data/customers.csv')
assert df.shape == (600,8)
print(df.head(3))

# Q02: 구조 확인
shape_result = df.shape
dtype_result = df.dtypes
assert shape_result == (600,8)
print(shape_result, dtype_result)

# Q03: 결측 확인
missing_counts = df.isna().sum().sort_values(ascending=False)
assert missing_counts['monthly_fee'] == 30
assert missing_counts['contract_type'] == 18
print(missing_counts)

# Q04: 조건 선택
selected = df.loc[df['tenure_months'] >= 12,['customer_id','monthly_fee','churn']]
assert list(selected.columns) == ['customer_id','monthly_fee','churn']
assert len(selected) == int((df['tenure_months']>=12).sum())
print(selected.head())

# Q05: 그룹 집계
contract_summary = df.groupby('contract_type',dropna=False).agg(
    customer_count=('customer_id','size'),churn_rate=('churn','mean'))
assert contract_summary['customer_count'].sum() == len(df)
print(contract_summary)

# Q06: 정의 위반 정리
cleaned = df.copy()
cleaned.loc[cleaned['monthly_fee']<0,'monthly_fee'] = np.nan
cleaned.loc[~cleaned['last_usage'].between(0,100),'last_usage'] = np.nan
assert np.isnan(cleaned.loc[0,'monthly_fee'])
assert np.isnan(cleaned.loc[1,'last_usage'])
assert cleaned.loc[2,'monthly_fee'] == 10000 and df.loc[0,'monthly_fee'] == -10

# Q07: 입력·타깃
numeric_cols = ['tenure_months','monthly_fee','support_calls','last_usage']
category_cols = ['contract_type','region']
X, y = cleaned[numeric_cols+category_cols], cleaned['churn']
assert X.shape == (600,6) and 'churn' not in X and 'customer_id' not in X

# Q08: 3분할
from sklearn.model_selection import train_test_split
X_dev,X_test,y_dev,y_test = train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)
X_train,X_val,y_train,y_val = train_test_split(X_dev,y_dev,test_size=0.25,random_state=42,stratify=y_dev)
assert (len(X_train),len(X_val),len(X_test)) == (360,120,120)
assert set(X_train.index).isdisjoint(X_val.index) and set(X_train.index).isdisjoint(X_test.index)
assert X_train.index.equals(y_train.index)

# Q09: 숫자 변환
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
numeric_prep = Pipeline([('imputer',SimpleImputer(strategy='median')),('scaler',StandardScaler())])
num_train = numeric_prep.fit_transform(X_train[numeric_cols])
num_val = numeric_prep.transform(X_val[numeric_cols])
num_test = numeric_prep.transform(X_test[numeric_cols])
assert np.allclose(num_train.mean(axis=0),0,atol=1e-6)
assert np.isfinite(num_val).all()

# Q10: 범주 변환
category_prep = Pipeline([('imputer',SimpleImputer(strategy='most_frequent')),
    ('encoder',OneHotEncoder(handle_unknown='ignore',sparse_output=False))])
cat_train = category_prep.fit_transform(X_train[category_cols])
cat_val = category_prep.transform(X_val[category_cols])
cat_test = category_prep.transform(X_test[category_cols])
train_data = np.column_stack([num_train,cat_train]).astype('float32')
val_data = np.column_stack([num_val,cat_val]).astype('float32')
test_data = np.column_stack([num_test,cat_test]).astype('float32')
assert train_data.shape == (360,9) and val_data.shape == test_data.shape == (120,9)

# Q11: 머신러닝 분류
from sklearn.linear_model import LogisticRegression
clf = LogisticRegression(max_iter=1000).fit(train_data,y_train)
pred = clf.predict(val_data)
prob = clf.predict_proba(val_data)[:,list(clf.classes_).index(1)]
assert len(pred) == len(prob) == 120 and clf.get_params()['max_iter'] == 1000

# Q12: 지표
from sklearn.metrics import accuracy_score,f1_score,roc_auc_score,confusion_matrix
accuracy = accuracy_score(y_val,pred)
f1 = f1_score(y_val,pred,zero_division=0)
auc = roc_auc_score(y_val,prob)
cm = confusion_matrix(y_val,pred,labels=[0,1])
assert cm.sum() == 120 and all(0<=v<=1 for v in (accuracy,f1,auc))
print(accuracy,f1,auc,cm)

# Q13: 딥러닝 분류
import tensorflow as tf
from lab import dataset
tf.keras.backend.clear_session()
tf.keras.utils.set_random_seed(42)
model = tf.keras.Sequential([tf.keras.layers.Input(shape=(train_data.shape[1],)),
    tf.keras.layers.Dense(16,activation='relu'),tf.keras.layers.Dense(1,activation='sigmoid')])
model.compile(optimizer=tf.keras.optimizers.Adam(0.01),loss='binary_crossentropy',metrics=['accuracy'])
history = model.fit(dataset(train_data,y_train.to_numpy(dtype='float32'),True),
    validation_data=dataset(val_data,y_val.to_numpy(dtype='float32')),epochs=4,verbose=0)
assert model.output_shape[-1] == 1 and len(history.history['loss']) == 4

# Q14: 딥러닝 평가·그림
from lab import dense_predict
dl_prob = dense_predict(model,val_data)
dl_pred = (dl_prob>=0.5).astype(int)
dl_f1 = f1_score(y_val,dl_pred,zero_division=0)
assert dl_pred.shape == (120,) and 0<=dl_f1<=1
plt.plot(history.history['loss'],label='train')
plt.plot(history.history['val_loss'],label='validation')
plt.xlabel('Epoch index'); plt.ylabel('Loss'); plt.legend(); plt.show(); plt.close('all')
print('Validation DL F1:',dl_f1)

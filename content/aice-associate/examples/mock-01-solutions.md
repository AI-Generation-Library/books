---
title: "1회 모의고사 해설"
description: ""
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
---

# 1회 모의고사 해설

같은 요구조건을 만족하는 다른 풀이도 가능하다. 검증의 점수는 가상 자료의 결과이며 공식 시험 성적이 아니다.

## 01. 자료 불러오기

파일과 변수명을 맞추고 인덱스용 열이 추가되지 않았는지 본다.

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from lab import ROOT
df = pd.read_csv(ROOT / 'data/customers.csv')
assert df.shape == (600,8)
print(df.head(3))
```

## 02. 구조 확인

shape는 속성이다. 자료형과 각 열의 의미를 구분한다.

```python
shape_result = df.shape
dtype_result = df.dtypes
assert shape_result == (600,8)
print(shape_result, dtype_result)
```

## 03. 결측 확인

범위 위반 정리 전 원자료의 결측을 계산한다.

```python
missing_counts = df.isna().sum().sort_values(ascending=False)
assert missing_counts['monthly_fee'] == 30
assert missing_counts['contract_type'] == 18
print(missing_counts)
```

## 04. 조건 선택

12개월 경계값을 포함하며 행과 열을 함께 선택한다.

```python
selected = df.loc[df['tenure_months'] >= 12,['customer_id','monthly_fee','churn']]
assert list(selected.columns) == ['customer_id','monthly_fee','churn']
assert len(selected) == int((df['tenure_months']>=12).sum())
print(selected.head())
```

## 05. 그룹 집계

size는 그룹 행 수이며 0·1 평균은 해당 표본의 이탈 비율이다.

```python
contract_summary = df.groupby('contract_type',dropna=False).agg(
    customer_count=('customer_id','size'),churn_rate=('churn','mean'))
assert contract_summary['customer_count'].sum() == len(df)
print(contract_summary)
```

## 06. 정의 위반 정리

고정된 데이터 사전 조건과 통계적 극단값을 구분한다.

```python
cleaned = df.copy()
cleaned.loc[cleaned['monthly_fee']<0,'monthly_fee'] = np.nan
cleaned.loc[~cleaned['last_usage'].between(0,100),'last_usage'] = np.nan
assert np.isnan(cleaned.loc[0,'monthly_fee'])
assert np.isnan(cleaned.loc[1,'last_usage'])
assert cleaned.loc[2,'monthly_fee'] == 10000 and df.loc[0,'monthly_fee'] == -10
```

## 07. 입력·타깃

ID·타깃을 입력에서 제외하고 순서를 보존한다.

```python
numeric_cols = ['tenure_months','monthly_fee','support_calls','last_usage']
category_cols = ['contract_type','region']
X, y = cleaned[numeric_cols+category_cols], cleaned['churn']
assert X.shape == (600,6) and 'churn' not in X and 'customer_id' not in X
```

## 08. 3분할

두 번째 비율은 남은 자료 기준이다.

```python
from sklearn.model_selection import train_test_split
X_dev,X_test,y_dev,y_test = train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)
X_train,X_val,y_train,y_val = train_test_split(X_dev,y_dev,test_size=0.25,random_state=42,stratify=y_dev)
assert (len(X_train),len(X_val),len(X_test)) == (360,120,120)
assert set(X_train.index).isdisjoint(X_val.index) and set(X_train.index).isdisjoint(X_test.index)
assert X_train.index.equals(y_train.index)
```

## 09. 숫자 변환

평가 집합에서는 transform만 사용한다.

```python
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
numeric_prep = Pipeline([('imputer',SimpleImputer(strategy='median')),('scaler',StandardScaler())])
num_train = numeric_prep.fit_transform(X_train[numeric_cols])
num_val = numeric_prep.transform(X_val[numeric_cols])
num_test = numeric_prep.transform(X_test[numeric_cols])
assert np.allclose(num_train.mean(axis=0),0,atol=1e-6)
assert np.isfinite(num_val).all()
```

## 10. 범주 변환

열의 수·순서가 모든 집합에서 동일해야 한다.

```python
category_prep = Pipeline([('imputer',SimpleImputer(strategy='most_frequent')),
    ('encoder',OneHotEncoder(handle_unknown='ignore',sparse_output=False))])
cat_train = category_prep.fit_transform(X_train[category_cols])
cat_val = category_prep.transform(X_val[category_cols])
cat_test = category_prep.transform(X_test[category_cols])
train_data = np.column_stack([num_train,cat_train]).astype('float32')
val_data = np.column_stack([num_val,cat_val]).astype('float32')
test_data = np.column_stack([num_test,cat_test]).astype('float32')
assert train_data.shape == (360,9) and val_data.shape == test_data.shape == (120,9)
```

## 11. 머신러닝 분류

predict와 predict_proba를 구분하고 classes_ 순서를 확인한다.

```python
from sklearn.linear_model import LogisticRegression
clf = LogisticRegression(max_iter=1000).fit(train_data,y_train)
pred = clf.predict(val_data)
prob = clf.predict_proba(val_data)[:,list(clf.classes_).index(1)]
assert len(pred) == len(prob) == 120 and clf.get_params()['max_iter'] == 1000
```

## 12. 지표

AUC에 확률을 제공하고 지표를 같은 자료에서 계산한다.

```python
from sklearn.metrics import accuracy_score,f1_score,roc_auc_score,confusion_matrix
accuracy = accuracy_score(y_val,pred)
f1 = f1_score(y_val,pred,zero_division=0)
auc = roc_auc_score(y_val,prob)
cm = confusion_matrix(y_val,pred,labels=[0,1])
assert cm.sum() == 120 and all(0<=v<=1 for v in (accuracy,f1,auc))
print(accuracy,f1,auc,cm)
```

## 13. 딥러닝 분류

이진 출력·손실을 맞춘다. 작은 epoch 수는 실행 연습 설정이다.

```python
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
```

## 14. 딥러닝 평가·그림

확률을 라벨로 바꾸고 두 손실 곡선을 표시한다. 테스트는 선택에 사용하지 않는다.

```python
from lab import dense_predict
dl_prob = dense_predict(model,val_data)
dl_pred = (dl_prob>=0.5).astype(int)
dl_f1 = f1_score(y_val,dl_pred,zero_division=0)
assert dl_pred.shape == (120,) and 0<=dl_f1<=1
plt.plot(history.history['loss'],label='train')
plt.plot(history.history['val_loss'],label='validation')
plt.xlabel('Epoch index'); plt.ylabel('Loss'); plt.legend(); plt.show(); plt.close('all')
print('Validation DL F1:',dl_f1)
```

---
title: "2회 모의고사 해설"
description: ""
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
---

# 2회 모의고사 해설

같은 요구조건을 만족하는 다른 풀이도 가능하다. 검증의 점수는 가상 자료의 결과이며 공식 시험 성적이 아니다.

## 01. 자료 불러오기

타깃 usage_hours와 식별자 record_id를 확인한다.

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from lab import ROOT
df = pd.read_csv(ROOT / 'data/service_usage.csv')
assert df.shape == (600,7)
print(df.head(3))
```

## 02. 품질 확인

가상 관측은 한 행씩 독립이며 ID가 고유하다.

```python
missing_counts = df.isna().sum()
duplicate_count = df['record_id'].duplicated().sum()
assert missing_counts['storage_gb'] == 24 and duplicate_count == 0
print(missing_counts,duplicate_count)
```

## 03. 집계

탐색용 집계이며 타깃 평균을 모델 입력에 다시 붙이지 않는다.

```python
plan_summary = df.groupby('plan').agg(count=('record_id','size'),mean_hours=('usage_hours','mean'))
assert plan_summary['count'].sum() == 600
print(plan_summary)
```

## 04. 조건 선택

이 문항의 선택 결과로 다음 모델 자료를 임의 축소하지 않는다.

```python
selected = df.loc[df['active_days']>=15,['record_id','active_days','usage_hours']]
assert len(selected) == int((df['active_days']>=15).sum())
print(selected.head())
```

## 05. 분포 그림

분포 탐색이며 모델을 고르기 위한 테스트 점수는 아니다.

```python
fig,ax = plt.subplots()
ax.hist(df['usage_hours'],bins=15)
ax.set_xlabel('Usage hours'); ax.set_ylabel('Count')
assert len(ax.patches) == 15
plt.show(); plt.close(fig)
```

## 06. 입력·타깃

타깃과 ID를 입력에서 제외한다.

```python
numeric_cols = ['active_users','active_days','storage_gb']
category_cols = ['plan','region']
X,y = df[numeric_cols+category_cols],df['usage_hours']
assert X.shape == (600,5) and 'usage_hours' not in X and 'record_id' not in X
```

## 07. 분할

이 자료는 독립 행이다. 실제 시계열의 시간 분할을 대체하지 않는다.

```python
from sklearn.model_selection import train_test_split
X_dev,X_test,y_dev,y_test = train_test_split(X,y,test_size=0.2,random_state=42)
X_train,X_val,y_train,y_val = train_test_split(X_dev,y_dev,test_size=0.25,random_state=42)
assert (len(X_train),len(X_val),len(X_test)) == (360,120,120)
assert X_train.index.equals(y_train.index)
```

## 08. 숫자 결측 대체

평가 집합의 중앙값을 따로 계산하지 않는다.

```python
from sklearn.impute import SimpleImputer
median_imputer = SimpleImputer(strategy='median')
num_train = median_imputer.fit_transform(X_train[numeric_cols])
num_val = median_imputer.transform(X_val[numeric_cols])
num_test = median_imputer.transform(X_test[numeric_cols])
assert np.isfinite(num_train).all() and np.isfinite(num_test).all()
```

## 09. 표준화

검증·테스트에서 fit하지 않는다.

```python
from sklearn.preprocessing import StandardScaler,OneHotEncoder
scaler = StandardScaler()
num_train = scaler.fit_transform(num_train)
num_val = scaler.transform(num_val)
num_test = scaler.transform(num_test)
assert np.allclose(num_train.mean(axis=0),0,atol=1e-6)
```

## 10. 원핫·결합

이 가상 자료의 범주에는 결측이 없다. 일반 자료는 결측 정책이 필요하다.

```python
encoder = OneHotEncoder(handle_unknown='ignore',sparse_output=False)
cat_train = encoder.fit_transform(X_train[category_cols])
cat_val = encoder.transform(X_val[category_cols])
cat_test = encoder.transform(X_test[category_cols])
train_data = np.column_stack([num_train,cat_train]).astype('float32')
val_data = np.column_stack([num_val,cat_val]).astype('float32')
test_data = np.column_stack([num_test,cat_test]).astype('float32')
assert train_data.shape == (360,8) and val_data.shape == test_data.shape == (120,8)
```

## 11. 회귀 학습

분류 라벨 대신 연속값을 예측한다.

```python
from sklearn.linear_model import LinearRegression
reg = LinearRegression().fit(train_data,y_train)
pred = reg.predict(val_data)
assert pred.shape == (120,)
assert np.isfinite(pred).all()
```

## 12. 오차 평가

오차의 단위를 확인하고 R²를 0~1로 강제하지 않는다.

```python
from sklearn.metrics import mean_absolute_error,root_mean_squared_error,r2_score
mae = mean_absolute_error(y_val,pred)
rmse = root_mean_squared_error(y_val,pred)
r2 = r2_score(y_val,pred)
residual = y_val.to_numpy()-pred
assert residual.shape == (120,) and mae>=0 and rmse>=0
print(mae,rmse,r2)
```

## 13. 딥러닝 회귀

타깃의 통계도 훈련에서만 계산한다.

```python
import tensorflow as tf
from lab import dataset
target_mean,target_std = y_train.mean(),y_train.std(ddof=0)
assert target_std>0
train_y = ((y_train-target_mean)/target_std).to_numpy(dtype='float32')
val_y = ((y_val-target_mean)/target_std).to_numpy(dtype='float32')
tf.keras.backend.clear_session(); tf.keras.utils.set_random_seed(42)
model = tf.keras.Sequential([tf.keras.layers.Input(shape=(train_data.shape[1],)),
    tf.keras.layers.Dense(16,activation='relu'),tf.keras.layers.Dense(1,activation='linear')])
model.compile(optimizer=tf.keras.optimizers.Adam(0.01),loss='mse')
history = model.fit(dataset(train_data,train_y,True),validation_data=dataset(val_data,val_y),epochs=4,verbose=0)
assert model.output_shape[-1]==1 and len(history.history['loss'])==4
```

## 14. 역변환·그림

표준화 손실을 시간 단위 오차로 해석하지 않고 역변환 후 평가한다.

```python
from lab import dense_predict
dl_pred = dense_predict(model,val_data)*target_std+target_mean
dl_rmse = root_mean_squared_error(y_val,dl_pred)
assert dl_pred.shape==(120,) and np.isfinite(dl_pred).all() and dl_rmse>=0
plt.scatter(y_val,dl_pred,alpha=0.5)
plt.xlabel('Actual usage hours'); plt.ylabel('Predicted usage hours')
plt.show(); plt.close('all')
print('Validation DL RMSE hours:',dl_rmse)
```

"""Author-created solution. Run from examples/. No external data or AI calls."""

# Q01: 자료 불러오기
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from lab import ROOT
df = pd.read_csv(ROOT / 'data/service_usage.csv')
assert df.shape == (600,7)
print(df.head(3))

# Q02: 품질 확인
missing_counts = df.isna().sum()
duplicate_count = df['record_id'].duplicated().sum()
assert missing_counts['storage_gb'] == 24 and duplicate_count == 0
print(missing_counts,duplicate_count)

# Q03: 집계
plan_summary = df.groupby('plan').agg(count=('record_id','size'),mean_hours=('usage_hours','mean'))
assert plan_summary['count'].sum() == 600
print(plan_summary)

# Q04: 조건 선택
selected = df.loc[df['active_days']>=15,['record_id','active_days','usage_hours']]
assert len(selected) == int((df['active_days']>=15).sum())
print(selected.head())

# Q05: 분포 그림
fig,ax = plt.subplots()
ax.hist(df['usage_hours'],bins=15)
ax.set_xlabel('Usage hours'); ax.set_ylabel('Count')
assert len(ax.patches) == 15
plt.show(); plt.close(fig)

# Q06: 입력·타깃
numeric_cols = ['active_users','active_days','storage_gb']
category_cols = ['plan','region']
X,y = df[numeric_cols+category_cols],df['usage_hours']
assert X.shape == (600,5) and 'usage_hours' not in X and 'record_id' not in X

# Q07: 분할
from sklearn.model_selection import train_test_split
X_dev,X_test,y_dev,y_test = train_test_split(X,y,test_size=0.2,random_state=42)
X_train,X_val,y_train,y_val = train_test_split(X_dev,y_dev,test_size=0.25,random_state=42)
assert (len(X_train),len(X_val),len(X_test)) == (360,120,120)
assert X_train.index.equals(y_train.index)

# Q08: 숫자 결측 대체
from sklearn.impute import SimpleImputer
median_imputer = SimpleImputer(strategy='median')
num_train = median_imputer.fit_transform(X_train[numeric_cols])
num_val = median_imputer.transform(X_val[numeric_cols])
num_test = median_imputer.transform(X_test[numeric_cols])
assert np.isfinite(num_train).all() and np.isfinite(num_test).all()

# Q09: 표준화
from sklearn.preprocessing import StandardScaler,OneHotEncoder
scaler = StandardScaler()
num_train = scaler.fit_transform(num_train)
num_val = scaler.transform(num_val)
num_test = scaler.transform(num_test)
assert np.allclose(num_train.mean(axis=0),0,atol=1e-6)

# Q10: 원핫·결합
encoder = OneHotEncoder(handle_unknown='ignore',sparse_output=False)
cat_train = encoder.fit_transform(X_train[category_cols])
cat_val = encoder.transform(X_val[category_cols])
cat_test = encoder.transform(X_test[category_cols])
train_data = np.column_stack([num_train,cat_train]).astype('float32')
val_data = np.column_stack([num_val,cat_val]).astype('float32')
test_data = np.column_stack([num_test,cat_test]).astype('float32')
assert train_data.shape == (360,8) and val_data.shape == test_data.shape == (120,8)

# Q11: 회귀 학습
from sklearn.linear_model import LinearRegression
reg = LinearRegression().fit(train_data,y_train)
pred = reg.predict(val_data)
assert pred.shape == (120,)
assert np.isfinite(pred).all()

# Q12: 오차 평가
from sklearn.metrics import mean_absolute_error,root_mean_squared_error,r2_score
mae = mean_absolute_error(y_val,pred)
rmse = root_mean_squared_error(y_val,pred)
r2 = r2_score(y_val,pred)
residual = y_val.to_numpy()-pred
assert residual.shape == (120,) and mae>=0 and rmse>=0
print(mae,rmse,r2)

# Q13: 딥러닝 회귀
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

# Q14: 역변환·그림
from lab import dense_predict
dl_pred = dense_predict(model,val_data)*target_std+target_mean
dl_rmse = root_mean_squared_error(y_val,dl_pred)
assert dl_pred.shape==(120,) and np.isfinite(dl_pred).all() and dl_rmse>=0
plt.scatter(y_val,dl_pred,alpha=0.5)
plt.xlabel('Actual usage hours'); plt.ylabel('Predicted usage hours')
plt.show(); plt.close('all')
print('Validation DL RMSE hours:',dl_rmse)

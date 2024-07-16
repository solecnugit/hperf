import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
from datetime import datetime, timedelta

data = pd.read_csv("timeseries.csv")
data['CPI'] = data['CYCLES'] / data['INSTRUCTIONS']

# 使用 prophet 训练和预测
prophet_df = pd.DataFrame()
prophet_df['ds'] = data['timestamp']
prophet_df['y'] = data['CPI']

# prophet 支持的时间格式为： YYYY-MM-DD HH:MM:SS
# 进行时间格式的转换
# 假定一个年月日日期
start_date = datetime(2000, 1, 1)

# 将浮点数时间戳转换为 datetime 类型
prophet_df['ds'] = prophet_df['ds'].apply(lambda x : start_date + timedelta(seconds=x))

# 计算80%的索引位置
cut_off_index = int(len(prophet_df) * 0.8)

# 分成训练集和测试集
train_df = prophet_df.iloc[:cut_off_index]
test_df = prophet_df.iloc[cut_off_index:]

print(f"训练集大小: {len(train_df)}")
print(f"测试集大小: {len(test_df)}")

# 初始化并拟合模型
model = Prophet()
model.fit(train_df)

# 创建未来数据框，包括测试集的日期
# 我们使用“秒”作为性能数据的时间间隔，因此 freq 设置为 s（秒）。
# 在不设置情况，是以 天 为单位
future = model.make_future_dataframe(periods=len(test_df), freq='s')
forecast = model.predict(future)

# 提取实际值和预测值
actual = test_df['y'].values
predicted = forecast['yhat'].iloc[-len(test_df):].values

# 计算评估指标
mae = mean_absolute_error(actual, predicted)
rmse = np.sqrt(mean_squared_error(actual, predicted))

print(f"Mean Absolute Error (MAE): {mae}")
print(f"Root Mean Squared Error (RMSE): {rmse}")

print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(len(test_df)))

import pandas as pd
import numpy as np

credit_data = pd.read_csv('./data/credit_card.csv',encoding="gb18030")
#print(credit_data.shape)
#丢弃逾期，呆账，强制停卡，退票，拒往记录为1、瑕疵户为2的记录
exp1 = (credit_data["逾期"] == 1) & (credit_data["呆账"] == 1)
exp2 = (credit_data["强制停卡记录"] == 1) & (credit_data["退票"] == 1)
exp3 = exp1 & exp2
exp4 = (credit_data["拒往记录"] == 1) & (credit_data["瑕疵户"] == 2)
exp = exp3 & exp4
credit = credit_data.loc[exp == False,:]
credit.to_csv('./data/credit1.csv')#保存成第一类
#print(credit.shape)
#丢弃呆账，强制停卡，退票为1，拒往记录为2的记录
exp5 = (credit_data["呆账"] == 1) & (credit_data["强制停卡记录"] == 1)
exp6 = (credit_data["退票"] == 1) & (credit_data["拒往记录"] == 2)
exp = exp5 & exp6
credit = credit_data.loc[exp == False,:]
credit.to_csv('./data/credit2.csv')#保存成第二类
#print(credit.shape)
#丢弃频率为5，刷卡金额不等于1的数据
exp7 = (credit_data["频率"] == 5) & (credit_data["月刷卡额"] == 1)
credit = credit_data.loc[exp7 == False,:]
credit.to_csv('./data/credit3.csv')#保存成第三类
#print(credit.shape)

from sklearn.preprocessing import StandardScaler
#根据特征瑕疵户，逾期，呆账，强制停卡记录，退票，拒往记录构建历史行为特征
credit_selection1 = credit_data[["瑕疵户","逾期","呆账","强制停卡记录","退票","拒往记录"]]
data1 = StandardScaler().fit_transform(credit_selection1)
#print(credit_selection1.head())
#print(data1[:5,:])
#根据特征借款余额，个人月收入，个人月开销，家庭月收入和月刷卡额构建经济风险情况特征
credit_selection2 = credit_data[["借款余额","个人月收入","个人月开销","家庭月收入","月刷卡额"]]
data2 = StandardScaler().fit_transform(credit_selection2)
#print(credit_selection2.head())
#print(data2[:5,:])
#根据特征职业，年龄，住家构建收入风险情况特征
credit_selection3 = credit_data[["职业","年龄","住家"]]
data3 = StandardScaler().fit_transform(credit_selection3)
#print(credit_selection3.head())
#print(data3[:5,:])

from sklearn.cluster import KMeans
kmeans_model1 = KMeans(n_clusters=5, n_jobs=4, random_state=123)
fit_kmeans1 = kmeans_model1.fit(data1)
print(kmeans_model1.cluster_centers_)#聚类中心
print(kmeans_model1.labels_)#查看样本的类别标签
r1 = pd.Series(kmeans_model1.labels_).value_counts()
print(r1)#每类的用户数目

kmeans_model2 = KMeans(n_clusters=5, n_jobs=4, random_state=123)
fit_kmeans2 = kmeans_model2.fit(data2)
print(kmeans_model2.cluster_centers_)#聚类中心
print(kmeans_model2.labels_)#查看样本的类别标签
r2 = pd.Series(kmeans_model2.labels_).value_counts()
print(r2)#每类的用户数目

kmeans_model3 = KMeans(n_clusters=5, n_jobs=4, random_state=123)
fit_kmeans3 = kmeans_model3.fit(data3)
print(kmeans_model3.cluster_centers_)#聚类中心
print(kmeans_model3.labels_)#查看样本的类别标签
r3 = pd.Series(kmeans_model3.labels_).value_counts()
print(r3)#每类的用户数目



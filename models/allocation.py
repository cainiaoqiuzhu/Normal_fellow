import logging as lg
import pandas as pd

def update_industry_analysis(unit_id_list, begin_date, end_date):
 """
 分析基金历史配置行业比例。
 目前仅支持申万1、2级行业.
 """
 for unit_id in unit_id_list:
     lg.info('updating industry analysis: %s...' % unit_id)
     data = tools.load_unit_stock_ims(unit_id, begin_date, end_date)
     if len(data) <= 0:
        lg.warning('unit %s unit_stock_ims found empty data', unit_id)
        continue

     # 添加行业信息
     data = tools.add_ind(data)

     # =====================================================================
     # 行业仓位明细
     # =====================================================================
     # 一级行业历史仓位
     ind_ts1 = data['weight'].groupby([data['date'], data['ind1']]).sum().reset_index()
     ind_ts1['ind1'] = tools.map_ind(ind_ts1['ind1'])
     ind_ts1.columns = ['date', 'ind_name', 'weight_ind']
     ind_ts1['ind_level'] = 1

     # 二级行业历史仓位
     ind_ts2 = data['weight'].groupby([data['date'], data['ind2']]).sum().reset_index()
     ind_ts2['ind2'] = tools.map_ind(ind_ts2['ind2'])
     ind_ts2.columns = ['date', 'ind_name', 'weight_ind']
     ind_ts2['ind_level'] = 2

     ind_ts = pd.concat([ind_ts1, ind_ts2])
     ind_ts['unit_id'] = unit_id
     ind_ts = ind_ts[['date', 'unit_id'] + list(ind_ts.columns[1:-1])]
     if len(ind_ts) <= 0:
         lg.warning('unit %s ind_ts found empty data', unit_id)
         continue
     # 输出结果
     tools_data.save(ind_ts, 'result/unit_allocation_ind_detail',
     primary_key=['date', 'unit_id', 'ind_name', 'ind_level'])

     # =====================================================================
     # 行业集中度
     # =====================================================================
     cr1 = ind_ts['weight_ind'].groupby([ind_ts['date'], ind_ts['ind_level']]).apply(
     lambda x: x[x.rank(ascending=False) <= 1].sum())
     cr3 = ind_ts['weight_ind'].groupby([ind_ts['date'], ind_ts['ind_level']]).apply(
     lambda x: x[x.rank(ascending=False) <= 3].sum())
     cr5 = ind_ts['weight_ind'].groupby([ind_ts['date'], ind_ts['ind_level']]).apply(
     lambda x: x[x.rank(ascending=False) <= 5].sum())
     cr = pd.concat([cr1, cr3, cr5], axis=1)
     cr.columns = ['cr1', 'cr3', 'cr5']
     cr = cr.reset_index()
     cr['unit_id'] = unit_id
     cr = cr[['date', 'unit_id'] + list(cr.columns[1:-1])]
     tools_data.save(cr, 'result/unit_allocation_ind_cr', primary_key=[
     'date', 'unit_id', 'ind_level'])
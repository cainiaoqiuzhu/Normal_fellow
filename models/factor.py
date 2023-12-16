# -*- coding: utf-8 -*-
"""
Created on Wed Aug 23 10:39:08 2023

计算基金因子暴露情况

@author: zhangshuai
"""

import numpy as np
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta

from libs import tools, tools_general
from libs import tools_data
from libs.log import lg


def calc_fund_factor(fac, weight, name):
    """
    用市值加权法，计算组合股票因子暴露。

    fac: T*N DataFrame
    weight: T*N DataFrame
    name: the factor's name
    """
    fac = fac[fac.index.isin(weight.index)] # 保留 fac 中与 weight 索引相匹配的部分
    fac[np.isinf(fac)] = np.nan #  将 fac 中的正无穷值（Inf）替换为 NaN
    fac = fac[fac.notnull().any(axis=1)] # 移除 fac 中任何行中包含 NaN 的行
    fac = tools_general.winsorize(tools_general.winsorize(fac, method=2,
                                                          axis=1), axis=1)
    # 对 fac 进行两次 Winsorize 处理，方法为 2，沿着水平轴（axis=1）进行。
    fac = fac.T[fac.columns.isin(weight.columns)].T # 保留 fac 中与 weight 列匹配的部分
    # 若组合里某只股票因子值缺失，则将其剔除，将剩余组合调整为100%仓位
    weight1 = weight.T[weight.columns.isin(fac.columns)].T # 保留 weight 中与更新后的 fac 列匹配的部分。
    weight1[fac.isnull()] = 0 # 将 weight1 中对应于 fac 中 NaN 值的元素置为 0
    weight1 /= pd.DataFrame([weight1.sum(axis=1)], index=weight1.columns).T # 将 weight1 按行标准化，使每行的权重总和为 1。
    fac_pt = (fac * weight1).sum(axis=1) # 计算调整后的因子组合的加权总和。
    fac_pt = fac_pt[weight1.sum(axis=1) > 0] # 移除权重为 0 的行。
    fac_pt.name = name # 为结果 Series 设置名称为传入的 name。
    return fac_pt 


def update_factor_basic(unit_id_list, begin_date, end_date):
    """
    股票基本信息的因子
    """
    # 将因子起始时间提前2周，以防止在mergeAHdata中ffill时缺失数据
    t0 = dt.datetime.strptime(begin_date, '%Y%m%d') - relativedelta(days=14)
    dates = tools.get_trading_days(begin_date, end_date)
    # 市值
    mv = tools_data.load('stock/derivative_a', t0, end_date,
                         pivot_columns=['date', 'stk_code', 'total_mv'])
    mv_hk = tools_data.load('stock/derivative_hk', t0, end_date,
                            pivot_columns=['date', 'stk_code', 'total_mv'])
    mv = tools.mergeAHdata(mv, mv_hk)
    float_mv = tools_data.load('stock/derivative_a', t0, end_date,
                               pivot_columns=['date', 'stk_code', 'float_mv'])
    float_mv_hk = tools_data.load('stock/derivative_hk', t0, end_date,
                                  pivot_columns=['date', 'stk_code', 'total_mv'])
    float_mv = tools.mergeAHdata(float_mv, float_mv_hk)
    mv_log = np.log(mv)
    float_mv_log = np.log(float_mv)

    # 上市时间
    list_years = tools_data.load('basic/basic_stock_a').set_index(
        'stk_code')['list_date'].astype('datetime64[ns]')
    # TODO：解决部分港股上市日期缺失的问题，如0291.HK、0004.HK
    list_years_hk = tools_data.load('basic/basic_stock_hk').set_index(
        'stk_code')['list_date'].astype('datetime64[ns]')
    list_years = pd.concat([list_years, list_years_hk])
    list_years = list_years[list_years.notnull()]
    temp = pd.DataFrame([dates], index=list_years.index).T
    list_years = pd.DataFrame([list_years], index=dates)
    list_years = (temp - list_years).apply(lambda x: x.dt.days) / 365.25
    list_years_log = np.log(list_years)

    for unit_id in unit_id_list:
        lg.info('updating factors of basic: %s...' % unit_id)
    # 获取个股仓位
    data = tools.load_unit_stock_ims(unit_id, begin_date, end_date)
    data = data[data['mv'] > 0]
    weight = data.pivot('date', 'stk_code', 'weight')
    # 计算组合因子
    # 市值
    fac_mv = calc_fund_factor(mv, weight, 'mv')
    fac_float_mv = calc_fund_factor(float_mv, weight, 'float_mv')
    fac_mv_log = calc_fund_factor(mv_log, weight, 'mv_log')
    fac_float_mv_log = calc_fund_factor(float_mv_log, weight, 'float_mv_log')
    # 上市时间
    fac_list_years = calc_fund_factor(list_years, weight, 'list_years')
    fac_list_years_log = calc_fund_factor(list_years_log, weight,
                                          'list_years_log')

    result = pd.concat([fac_mv, fac_float_mv, fac_mv_log, fac_float_mv_log,
                        fac_list_years, fac_list_years_log], axis=1)
    result['unit_id'] = unit_id
    result = pd.concat([result['unit_id'], result.iloc[:, :-1]], axis=1)
    result.index.name = 'date'
    result = result.reset_index()
    result.fillna(0, inplace=True)
    tools_data.save(result, 'result/unit_factor_basic', primary_key=[
        'date', 'unit_id'])


def update_factor_tech(unit_id_list, begin_date, end_date):
    """
    技术因子
    """
    t0 = dt.datetime.strptime(begin_date, '%Y%m%d') - relativedelta(months=13)
    adj_close = tools_data.load('stock/quote_a', t0, end_date, pivot_columns=[
        'date', 'stk_code', 'adj_close'])
    adj_close_hk = tools_data.load('stock/quote_hk', t0, end_date,
                                   pivot_columns=['date', 'stk_code', 'adj_close'])
    adj_close = tools.mergeAHdata(adj_close, adj_close_hk)
    distance_1y = adj_close / adj_close.rolling(243, min_periods=1).max() - 1
    ret = adj_close.pct_change()
    vol = tools_data.load('stock/quote_a', t0, end_date, pivot_columns=[
        'date', 'stk_code', 'vol'])
    vol_hk = tools_data.load('stock/quote_hk', t0, end_date, pivot_columns=[
        'date', 'stk_code', 'vol'])
    vol = tools.mergeAHdata(vol, vol_hk)
    free_share = tools_data.load('stock/derivative_a', t0, end_date,
                                 pivot_columns=['date', 'stk_code', 'free_share'])
    # TODO: 这里暂用float_share替代，将来获得港股free_share之后再更改
    free_share_hk = tools_data.load('stock/derivative_hk', t0, end_date,
                                    pivot_columns=['date', 'stk_code', 'float_share'])
    free_share = tools.mergeAHdata(free_share, free_share_hk)
    turn = vol / free_share

    for unit_id in unit_id_list:
        lg.info('updating factors of tech: %s...' % unit_id)
    # 获取个股仓位
    data = tools.load_unit_stock_ims(unit_id, begin_date, end_date)
    data = data[data['mv'] > 0]
    weight = data.pivot('date', 'stk_code', 'weight')
    # 计算组合因子
    # 距1年最高价距离
    fac_distance_1y = calc_fund_factor(distance_1y, weight, 'distance_1y')
    result = pd.concat([fac_distance_1y, ], axis=1)
    for T in [20, 40, 60, 90, 120, 243]:
    # 动量
    mom = adj_close.pct_change(T)
    fac_mom = calc_fund_factor(mom, weight, name='mom%s' % T)
    # 波动率
    std = ret.rolling(T).std() * 243 ** 0.5
    fac_std = calc_fund_factor(std, weight, name='std%s' % T)
    # 换手率
    turn_tmp = turn.rolling(T).mean()
    fac_turn = calc_fund_factor(turn_tmp, weight, name='turn%s' % T)
    result = pd.concat([result, fac_mom, fac_std, fac_turn], axis=1)
    result['unit_id'] = unit_id
    result = pd.concat([result['unit_id'], result.iloc[:, :-1]], axis=1)
    result.index.name = 'date'
    result = result.reset_index()
    result.fillna(0, inplace=True)
    tools_data.save(result, 'result/unit_factor_tech', primary_key=[
        'date', 'unit_id'])


def update_factor_value(unit_id_list, begin_date, end_date):
    """
    估值因子
    """
    t0 = dt.datetime.strptime(begin_date, '%Y%m%d') - relativedelta(months=13)
    # PE
    ep_ttm = tools_data.load('stock/derivative_a', t0, end_date,
                             pivot_columns=['date', 'stk_code', 'pe_ttm'])
    ep_ttm_hk = tools_data.load('stock/derivative_hk', t0, end_date,
                                pivot_columns=['date', 'stk_code', 'pe_ttm'])
    ep_ttm = 1 / tools.mergeAHdata(ep_ttm, ep_ttm_hk)
    # PB
    bp_lf = tools_data.load('stock/derivative_a', t0, end_date,
                            pivot_columns=['date', 'stk_code', 'pb_lf'])
    bp_hk = tools_data.load('stock/derivative_hk', t0, end_date,
                            pivot_columns=['date', 'stk_code', 'pb'])
    bp_lf = 1 / tools.mergeAHdata(bp_lf, bp_hk)
    # PS
    sp_ttm = tools_data.load('stock/derivative_a', t0, end_date,
                             pivot_columns=['date', 'stk_code', 'ps_ttm'])
    sp_ttm_hk = tools_data.load('stock/derivative_hk', t0, end_date,
                                pivot_columns=['date', 'stk_code', 'ps_ttm'])
    sp_ttm = 1 / tools.mergeAHdata(sp_ttm, sp_ttm_hk)

    for unit_id in unit_id_list:
        lg.info('updating factors of value: %s...' % unit_id)
    # 获取个股仓位
    data = tools.load_unit_stock_ims(unit_id, begin_date, end_date)
    data = data[data['mv'] > 0]
    weight = data.pivot('date', 'stk_code', 'weight')
    # 计算组合因子
    fac_ep_ttm = calc_fund_factor(ep_ttm, weight, 'ep_ttm')
    fac_bp_lf = calc_fund_factor(bp_lf, weight, 'bp_lf')
    fac_sp_ttm = calc_fund_factor(sp_ttm, weight, 'sp_ttm')

    result = pd.concat([fac_ep_ttm, fac_bp_lf, fac_sp_ttm], axis=1)
    result['unit_id'] = unit_id
    result = pd.concat([result['unit_id'], result.iloc[:, :-1]], axis=1)
    result.index.name = 'date'
    result = result.reset_index()
    result.fillna(0, inplace=True)
    tools_data.save(result, 'result/unit_factor_value', primary_key=[
        'date', 'unit_id'])


def update_factor_barra_cne5(unit_id_list, begin_date, end_date):
    """
    更新barra cne5风格因子
    """
    barra = tools_data.load('stock/barra_factor_cne5', begin_date, end_date)
    fields = ['beta', 'momentum', 'size', 'earnyild', 'resvol',
              'growth', 'btop', 'leverage', 'liquidty', 'sizenl']
    for unit_id in unit_id_list:
        lg.info('updating factors of barra_cne5: %s...' % unit_id)
    # 获取个股仓位
    data = tools.load_unit_stock_ims(unit_id, begin_date, end_date)
    data = data[data['mv'] > 0]
    data = data.merge(barra, how='left')
    # 去掉barra因子缺失值，如港股
    data = data[data['size'].notnull()]
    # 将个股因子按照股票权重加权
    fac_weighted = data[fields] * pd.DataFrame([data['weight']], index=fields).T
    # 将股票组合权重归一化
    result = fac_weighted.groupby(data['date']).sum() / pd.DataFrame([
        data['weight'].groupby(data['date']).sum()], index=fields).T
    result['unit_id'] = unit_id
    result = pd.concat([result['unit_id'], result.iloc[:, :-1]], axis=1)
    result.index.name = 'date'
    result = result.reset_index()
    tools_data.save(result, 'result/unit_factor_barra_cne5', primary_key=[
        'date', 'unit_id'])

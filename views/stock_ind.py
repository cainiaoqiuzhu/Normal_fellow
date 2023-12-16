# coding: utf-8

from flask import Blueprint, request

from libs.utils import get_args, task_response
from libs.log import lg
from models import factor_ims
from models import rawdata_basic, rawdata_stock
from models import allocation, factor
from models import unit

task = bpt = Blueprint('task', __name__)

FACTOR_MAP = {
    # 原始数据
    'rawdata_basic.update_calender':
        lambda unit_id_list, begin_date, end_date: rawdata_basic.update_calender(begin_date, end_date),
    'rawdata_basic.update_stock_description':
        lambda unit_id_list, begin_date, end_date: rawdata_basic.update_stock_description(),
    'rawdata_stock.update_quote_a':
        lambda unit_id_list, begin_date, end_date: rawdata_stock.update_quote_a(begin_date, end_date),
    'rawdata_stock.update_derivative_a':
        lambda unit_id_list, begin_date, end_date: rawdata_stock.update_derivative_a(begin_date, end_date),
    'rawdata_stock.update_quote_hk':
        lambda unit_id_list, begin_date, end_date: rawdata_stock.update_quote_hk(begin_date, end_date),
    'rawdata_stock.update_derivative_hk':
        lambda unit_id_list, begin_date, end_date: rawdata_stock.update_derivative_hk(begin_date, end_date),
    'rawdata_stock.update_industry':
        lambda unit_id_list, begin_date, end_date: rawdata_stock.update_industry(begin_date, end_date),
    'rawdata_stock.update_consensus_forecast_a':
        lambda unit_id_list, begin_date, end_date: rawdata_stock.update_consensus_forecast_a(begin_date, end_date),
    'rawdata_stock.update_consensus_forecast_hk':
        lambda unit_id_list, begin_date, end_date: rawdata_stock.update_consensus_forecast_hk(begin_date, end_date),
    'rawdata_stock.update_dividend_a':
        lambda unit_id_list, begin_date, end_date: rawdata_stock.update_dividend_a(begin_date, end_date),
    'rawdata_stock.update_dividend_hk':
        lambda unit_id_list, begin_date, end_date: rawdata_stock.update_dividend_hk(begin_date, end_date),
    'rawdata_stock.update_barra':
        lambda unit_id_list, begin_date, end_date: rawdata_stock.update_barra(begin_date, end_date),

    # 计算组合仓位信息
    'allocation.update_position_analysis':
        lambda unit_id_list, begin_date, end_date: allocation.update_position_analysis(unit_id_list, begin_date,
                                                                                       end_date),
    'allocation.update_industry_analysis':
        lambda unit_id_list, begin_date, end_date: allocation.update_industry_analysis(unit_id_list, begin_date,
                                                                                       end_date),

    # 计算股票组合因子信息
    'factor.update_factor_basic':
        lambda unit_id_list, begin_date, end_date: factor.update_factor_basic(unit_id_list, begin_date, end_date),
    'factor.update_factor_tech':
        lambda unit_id_list, begin_date, end_date: factor.update_factor_tech(unit_id_list, begin_date, end_date),
    'factor.update_factor_value':
        lambda unit_id_list, begin_date, end_date: factor.update_factor_value(unit_id_list, begin_date, end_date),
    'factor.update_factor_barra_cne5':
        lambda unit_id_list, begin_date, end_date: factor.update_factor_barra_cne5(unit_id_list, begin_date, end_date),
}

USER_CODE = 'shawn'


@bpt.route('/update/factor', methods=['GET', 'POST'])
@task_response
def update_factor():
    ''' 更新基础指标与市场信息 '''
    args = get_args(request.json, skip_unit=True)
    if isinstance(args, tuple):
        success, message = args
        return {'code': 200, 'success': success, 'message': message, 'data': []}
    factor_code = request.json.get('factor_code')

    factor_method = FACTOR_MAP.get(factor_code)
    if not factor_method:
        return {'code': 200, 'success': False, 'message': '错误的factor_code', 'data': []}

    unit_id_list = [unit_info.l_asset_id for _, unit_info in unit.get_unit_list(USER_CODE).iterrows()]

    def inner_task():

        factor_method(unit_id_list, args['begin_date'], args['end_date'])
        return {'code': 200, 'success': True, 'message': '执行成功', 'data': []}

    return {'func': inner_task}


@bpt.route('/update/ims', methods=['GET', 'POST'])
@task_response
def update_ims():
    ''' 更新IMS持仓信息 '''
    args = get_args(request.json, skip_unit=True)
    if isinstance(args, tuple):
        success, message = args
        return {'code': 200, 'success': success, 'message': message, 'data': []}

    unit_id_list = [unit_info.l_asset_id for _, unit_info in unit.get_unit_list(USER_CODE).iterrows()]

    def inner_task():

        for index, unit_id in enumerate(unit_id_list):
        lg.info('update %s %s', index, unit_id)
        factor_ims.update_unit_ims(unit_id, args['begin_date'], args['end_date'])
        factor_ims.update_unit_stock_ims(unit_id, args['begin_date'], args['end_date'])
        return {'code': 200, 'success': True, 'message': '执行成功', 'data': []}

    return {'func': inner_task}

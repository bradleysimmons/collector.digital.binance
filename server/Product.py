import talib
import numpy
from helpers import calculate_delta, f_talib, band, group_sma_o_p
from decimal import Decimal
import statistics

class Product():
    def __init__(self, args):
        self.id = args['id']
        self.symbol = args['symbol']
        self.data = {'id': args['id']}
        self.candles = {1: [], 5: [], 15: [], 30: [], 60: [], 360: []}
        self.pattern_predictions = args['pattern_predictions']
        self.current_candle_starts = {1: None, 5: None, 15: None, 30: None, 60: None, 360: None}

    def update_data(self, x):
        if x.get('e') == '24hrTicker':
            self.data.update(x)
        if x.get('e') == 'kline':
            self.update_candles(x)

    def update_data_from_candles(self, interval):
        pattern, target, is_quality = self.get_price_target_info(interval)
        self.data.update({
            f'{str(interval)}_p': self.candles[interval][-1]['p'],
            f'{str(interval)}_sma': self.candles[interval][-1]['sma'],
            f'{str(interval)}_sma_o_p': self.candles[interval][-1]['sma_o_p'],
            f'{str(interval)}_p_dlt': self.candles[interval][-1]['p_dlt'],
            f'{str(interval)}_macdhist': self.candles[interval][-1]['macdhist'],
            f'{str(interval)}_vsma': self.candles[interval][-1]['vsma'],
            f'{str(interval)}_obv': self.candles[interval][-1]['obv'],
            f'{str(interval)}_obv_o_vsma': self.candles[interval][-1]['obv_o_vsma'],
            f'{str(interval)}_v_o_vsma': self.candles[interval][-1]['v_o_vsma'],
            f'{str(interval)}_obv_o_vsma_stddevs': self.candles[interval][-1]['obv_o_vsma_stddevs'],
            f'{str(interval)}_v_o_vsma_stddevs': self.candles[interval][-1]['v_o_vsma_stddevs'],
            f'{str(interval)}_p_dict_keys': self.candles[interval][-1]['p_dict_keys'],
            f'{str(interval)}_best_battern': pattern,
            f'{str(interval)}_target': target,
            f'{str(interval)}_is_quality': is_quality
        })

    def get_price_target_info(self, interval):
        pattern = None
        target = None
        is_quality = None
        if len(self.candles[interval][-1]['p_dict_keys']):
            keys = self.candles[interval][-1]['p_dict_keys']
            prediction_data = [self.pattern_predictions.get_data(interval).get(k) for k in keys]
            prediction_data = [x for x in prediction_data if x]
            if len(prediction_data):
                sorted_best_pattern = sorted(prediction_data, key=lambda x:x['std_dev'])
                best_pattern = sorted_best_pattern[0]
                target = best_pattern['avg']
                pattern = best_pattern['key']
                is_quality = self.pattern_predictions.is_quality_pattern(pattern, interval)
        return pattern, target, is_quality
        

    def update_candles(self, x):
        interval_dict = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30
        }
        interval = interval_dict[x['k']['i']]
        if (not self.current_candle_starts[interval] 
            or x['k']['t'] > self.current_candle_starts[interval]):
            self.begin_new_candle(x['k']['t'], interval)
        self.candles[interval][-1].update({
            'o': Decimal(x['k']['o']),
            'h': Decimal(x['k']['h']),
            'l': Decimal(x['k']['l']),
            'c': Decimal(x['k']['c']),
            'v': Decimal(x['k']['v'])
        })

    def begin_new_candle(self, begin_time, interval):
        self.current_candle_starts[interval] = begin_time
        self.update_patterns(interval)
        self.update_calculations(interval)
        self.update_pattern_dict_keys(interval)
        self.update_pattern_predictions(interval)
        self.update_data_from_candles(interval)
        self.candles[interval].pop(0)
        self.candles[interval].append({})

    def get_data(self):
        return self.data

    def update_historical_candles(self, data, interval):
        if not data: return
        self.candles[interval] = [{
            'o': Decimal(x[1]),
            'h': Decimal(x[2]),
            'l': Decimal(x[3]),
            'c': Decimal(x[4]),
            'v': Decimal(x[5]),
        } for x in data]
        self.current_candle_starts[interval] = data[-1][0]
        self.update_historical_patterns(interval)
        self.update_historical_calculations(interval)
        self.update_historical_pattern_dict_keys(interval)
        self.update_historical_pattern_predictions(interval)

    def get_pattern_inputs(self, interval):
        return {
            'o': numpy.array([float(x['o']) for x in self.candles[interval]]),
            'h': numpy.array([float(x['h']) for x in self.candles[interval]]),
            'l': numpy.array([float(x['l']) for x in self.candles[interval]]),
            'c': numpy.array([float(x['c']) for x in self.candles[interval]]),
            'v': numpy.array([float(x['v']) for x in self.candles[interval]])
        }
########## stream
    def update_patterns(self, interval):
        inputs = self.get_pattern_inputs(interval)
        patterns_dict = {}
        for candle in talib.get_function_groups()['Pattern Recognition']:
            score = getattr(talib.stream, candle)(inputs['o'], inputs['h'], inputs['l'], inputs['c'])
            if score: patterns_dict.update({candle: score})
        self.candles[interval][-1]['p'] = patterns_dict

    def update_calculations(self, interval):
        inputs = self.get_pattern_inputs(interval)
        sma = f_talib(talib.stream.SMA(inputs['c']))
        macd, macdsignal, macdhist = talib.stream.MACD(inputs['c'])
        macd = f_talib(macd)
        macdsignal = f_talib(macdsignal)
        macdhist = f_talib(macdhist)
        vsma = f_talib(talib.stream.SMA(inputs['v']))
        obv = f_talib(talib.OBV(inputs['c'], inputs['v'])[-1])
        candle = self.candles[interval][-1]
        candle['sma'] = sma
        candle['sma_o_p'] = group_sma_o_p(calculate_delta(sma, candle['c'])) if sma else None
        p_dlt_band_dict = {
            1: .05,
            5: .1,
            15: .25,
            30: .5
        }
        candle['p_dlt'] = band(calculate_delta(candle['o'], candle['c']), p_dlt_band_dict[interval]) if candle['o'] and candle['c'] else None
        candle['macdhist'] = band(macdhist, 5) if macdhist else None
        candle['vsma'] = vsma if vsma else None
        candle['obv'] = obv if obv else None
        candle['obv_o_vsma'] = calculate_delta(obv, vsma) if obv and vsma else None
        candle['v_o_vsma'] = calculate_delta(candle['v'], vsma) if candle['v'] and vsma else None
            
        ######## break out to function
        obv_o_vsma_values = [x['obv_o_vsma'] for x in self.candles[interval] if x.get('obv_o_vsma')]
        if len(obv_o_vsma_values):
            obv_o_vsma_mean = sum(obv_o_vsma_values) / len(obv_o_vsma_values)
            obv_o_vsma_stddev = statistics.pstdev(obv_o_vsma_values)
            candle = self.candles[interval][-1]
            if candle.get('obv_o_vsma'):
                obv_o_vsma_stddevs = round((abs(obv_o_vsma_mean - candle['obv_o_vsma']) / obv_o_vsma_stddev))
                if candle['obv'] < candle['vsma']:
                    candle['obv_o_vsma_stddevs'] = obv_o_vsma_stddevs * -1
                else: candle['obv_o_vsma_stddevs'] = obv_o_vsma_stddevs
            else: candle['obv_o_vsma_stddevs'] = None
        else: 
            self.candles[interval][-1]['obv_o_vsma_stddevs'] = None

        v_o_vsma_values = [x['v_o_vsma'] for x in self.candles[interval] if x.get('v_o_vsma')]
        if len(v_o_vsma_values):
            v_o_vsma_mean = sum(v_o_vsma_values) / len(v_o_vsma_values)
            v_o_vsma_stddev = statistics.pstdev(v_o_vsma_values)
            candle = self.candles[interval][-1]
            if candle.get('v_o_vsma'):
                v_o_vsma_stddevs = round((abs(v_o_vsma_mean - candle['v_o_vsma']) / v_o_vsma_stddev))
                if candle['v'] < candle['vsma']:
                    candle['v_o_vsma_stddevs'] = v_o_vsma_stddevs * -1
                else: candle['v_o_vsma_stddevs'] = v_o_vsma_stddevs
            else: candle['v_o_vsma_stddevs'] = None
        else: 
            self.candles[interval][-1]['obv_o_vsma_stddevs'] = None

    def update_pattern_dict_keys(self, interval):
        candle = self.candles[interval][-1]
        candle['p_dict_keys'] = []
        if candle.get('sma_o_p'):
            for k in candle['p'].keys():
                key = (
                    k + 
                    str(candle['p'][k]) + '_' +
                    str(candle['sma_o_p']) + '_' +
                    str(candle['p_dlt']) + '_' + 
                    str(candle['v_o_vsma_stddevs'])

                )
                candle['p_dict_keys'].append(key)
            else:
                key = (
                    str(candle['sma_o_p']) + '_' +
                    str(candle['p_dlt']) + '_' + 
                    str(candle['v_o_vsma_stddevs'])

                )
                candle['p_dict_keys'].append(key)

    def update_pattern_predictions(self, interval):
        candle = self.candles[interval][-2]
        if candle['p_dict_keys']:
            price_delta = calculate_delta(candle['c'], self.candles[interval][-1]['c'])
            for key in candle['p_dict_keys']:
                self.pattern_predictions.update_data(key, price_delta, interval)


########## historical
    def update_historical_patterns(self, interval):
        inputs = self.get_pattern_inputs(interval)
        candle_patterns_dicts = [{} for x in range(len(inputs['o']))]
        for candle in talib.get_function_groups()['Pattern Recognition']:
            for i, score in enumerate(getattr(talib, candle)(inputs['o'], inputs['h'], inputs['l'], inputs['c'])):
                if score: candle_patterns_dicts[i].update({candle: score})
        for i in range(len(self.candles[interval])):
            self.candles[interval][i]['p'] = candle_patterns_dicts[i]

    def update_historical_calculations(self, interval):
        inputs = self.get_pattern_inputs(interval)
        sma = [f_talib(x) for x in talib.SMA(inputs['c'])]
        macd, macdsignal, macdhist = talib.MACD(inputs['c'])
        macd = [f_talib(x) for x in macd]
        macdsignal = [f_talib(x) for x in macdsignal]
        macdhist = [f_talib(x) for x in macdhist]
        vsma = [f_talib(x) for x in talib.SMA(inputs['v'])]
        obv = [f_talib(x) for x in talib.OBV(inputs['c'], inputs['v'])]
        for i in range(len(self.candles[interval])):
            candle = self.candles[interval][i]
            candle['sma'] = sma[i]
            candle['sma_o_p'] = group_sma_o_p(calculate_delta(sma[i], candle['c'])) if sma[i] else None
            p_dlt_band_dict = {
                1: .05,
                5: .1,
                15: .25,
                30: .5
            }
            candle['p_dlt'] = band(calculate_delta(candle['o'], candle['c']), p_dlt_band_dict[interval]) if candle['o'] and candle['c'] else None
            candle['macdhist'] = band(macdhist[i], 5) if macdhist[i] else None
            candle['vsma'] = vsma[i] if vsma[i] else None
            candle['obv'] = obv[i] if obv[i] else None
            candle['obv_o_vsma'] = calculate_delta(obv[i], vsma[i]) if obv[i] and vsma[i] else None
            candle['v_o_vsma'] = calculate_delta(candle['v'], vsma[i]) if candle['v'] and vsma[i] else None

        ######## break out to function
        obv_o_vsma_values = [x['obv_o_vsma'] for x in self.candles[interval] if x.get('obv_o_vsma')]
        if len(obv_o_vsma_values):
            obv_o_vsma_mean = sum(obv_o_vsma_values) / len(obv_o_vsma_values)
            obv_o_vsma_stddev = statistics.pstdev(obv_o_vsma_values)
            for i in range(len(self.candles[interval])):
                candle = self.candles[interval][i]
                if candle.get('obv_o_vsma'):
                    obv_o_vsma_stddevs = round((abs(obv_o_vsma_mean - candle['obv_o_vsma']) / obv_o_vsma_stddev))
                    if candle['obv'] < candle['vsma']:
                        candle['obv_o_vsma_stddevs'] = obv_o_vsma_stddevs * -1
                    else: candle['obv_o_vsma_stddevs'] = obv_o_vsma_stddevs
                else: candle['obv_o_vsma_stddevs'] = None
        else: 
            for i in range(len(self.candles[interval])): 
                self.candles[interval][i]['obv_o_vsma_stddevs'] = None

        v_o_vsma_values = [x['v_o_vsma'] for x in self.candles[interval] if x.get('v_o_vsma')]
        if len(v_o_vsma_values):
            v_o_vsma_mean = sum(v_o_vsma_values) / len(v_o_vsma_values)
            v_o_vsma_stddev = statistics.pstdev(v_o_vsma_values)
            for i in range(len(self.candles[interval])):
                candle = self.candles[interval][i]
                if candle.get('v_o_vsma'):
                    v_o_vsma_stddevs = round((abs(v_o_vsma_mean - candle['v_o_vsma']) / v_o_vsma_stddev))
                    if candle['v'] < candle['vsma']:
                        candle['v_o_vsma_stddevs'] = v_o_vsma_stddevs * -1
                    else: candle['v_o_vsma_stddevs'] = v_o_vsma_stddevs
                else: candle['v_o_vsma_stddevs'] = None
        else: 
            for i in range(len(self.candles[interval])): 
                self.candles[interval][i]['obv_o_vsma_stddevs'] = None

    def update_historical_pattern_dict_keys(self, interval):
        for i in range(len(self.candles[interval])):
            candle = self.candles[interval][i]
            candle['p_dict_keys'] = []
            if not candle.get('sma_o_p'): continue
            for k in candle['p'].keys():
                key = (
                    k + 
                    str(candle['p'][k]) + '_' +
                    str(candle['sma_o_p']) + '_' +
                    str(candle['p_dlt']) + '_' + 
                    str(candle['v_o_vsma_stddevs'])

                )
                candle['p_dict_keys'].append(key)
            else:
                key = (
                    str(candle['sma_o_p']) + '_' +
                    str(candle['p_dlt']) + '_' + 
                    str(candle['v_o_vsma_stddevs'])

                )
                candle['p_dict_keys'].append(key)

    def update_historical_pattern_predictions(self, interval):
        for i in range(len(self.candles[interval])):
            candle = self.candles[interval][i]
            if (candle['p_dict_keys']
                and len(self.candles[interval]) > i+1):
                price_delta = calculate_delta(candle['c'], self.candles[interval][i+1]['c'])
                for key in candle['p_dict_keys']:
                    self.pattern_predictions.update_data(key, price_delta, interval)











  
import collections
import statistics

class PatternPredictions():
    def __init__(self):
        self.data = {1: {}, 5: {}, 15: {}, 30: {}, 60: {}, 360: {}}
        self.meta = {1: {}, 5: {}, 15: {}, 30: {}, 60: {}, 360: {}}

    def update_data(self, key, price_delta, interval):
        if not self.data[interval].get(key): self.data[interval][key] = {'key': key,
                                                                            'list': [], 
                                                                            'avg': None,
                                                                            'std_dev': None,
                                                                            'down_std_dev': None,
                                                                            'up_std_dev': None,
                                                                            'pct_up': None,
                                                                            'pct_down': None,
                                                                            'high': None,
                                                                            'low': None}
        pattern_data = self.data[interval][key]
        pattern_data['list'].append(price_delta)
        pattern_data['avg'] = sum(pattern_data['list']) / len(pattern_data['list'])
        pattern_data['std_dev'] = statistics.pstdev(pattern_data['list'])
        pattern_data['down_std_dev'] = pattern_data['avg'] - pattern_data['std_dev']
        pattern_data['up_std_dev'] = pattern_data['avg'] + pattern_data['std_dev']
        pattern_data['pct_up'] = sum([1 if x > 0 else 0 for x in pattern_data['list']]) / len(pattern_data['list'])
        pattern_data['pct_down'] = sum([1 if x < 0 else 0 for x in pattern_data['list']]) / len(pattern_data['list'])
        pattern_data['high'] = max(pattern_data['list'])
        pattern_data['low'] = min(pattern_data['list'])
        self.set_meta(interval)

    def get_data(self, interval):
        return self.data[interval]

    def set_meta(self, interval):
        standard_deviations = [x['std_dev'] for x in self.data[interval].values()]
        self.meta[interval]['avg_standard_deviations'] = sum(standard_deviations) / len(standard_deviations)

        list_lengths = [len(x['list']) for x in self.data[interval].values()]
        self.meta[interval]['avg_list_length'] = sum(list_lengths) / len(list_lengths)

    def is_quality_pattern(self, pattern, interval):
        if (self.data[interval][pattern]['std_dev'] < self.meta[interval]['avg_standard_deviations']
            and len(self.data[interval][pattern]['list']) > self.meta[interval]['avg_list_length']
            and (self.data[interval][pattern]['down_std_dev'] > 0
                or self.data[interval][pattern]['up_std_dev'] < 0)):
            return True
        elif (self.data[interval][pattern]['down_std_dev'] > .5
                and self.data[interval][pattern]['pct_up'] == 1
                and len(self.data[interval][pattern]['list']) > 1):
            return True
        elif (self.data[interval][pattern]['up_std_dev'] < -.5
                and self.data[interval][pattern]['pct_down'] == 1
                and len(self.data[interval][pattern]['list']) > 1):
            return True
        else: return False



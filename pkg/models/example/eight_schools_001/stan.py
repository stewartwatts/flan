import os
from pkg.analysis import ModelSpec, StanAnalysis

# get category and model_name from the file's path
category, model_name = os.path.dirname(os.path.realpath(__file__)).split("/")[-2:]

class NewSpec(ModelSpec):
    """
    1. Implement `build_data`
    2. Make default args for `single_params`, `param_pairs`, `param_groups`
    """
    def __init__(self, category, model_name, 
                 single_params=["mu", "tau", "lp__"], 
                 param_pairs=[("mu", "tau"), ("mu", "lp__")], 
                 param_groups={"various": ["mu", "tau", "lp__"]}): 
        super(NewSpec, self).__init__(category, model_name,
                                      single_params=single_params,
                                      param_pairs=param_pairs,
                                      param_groups=param_groups)

    def build_data(self):
        """override"""
        data = {
            "J": 8, 
            "y": [28, 8, -3, 7, -1, 1, 18, 12],
            "sigma": [15, 10, 16, 11, 9, 11, 10, 18],
        }
        self.data = data


def main():
    model_spec = NewSpec(category, model_name)
    # adjust inference settings as needed
    sampling_args = {}
    analysis = StanAnalysis(model_spec, sampling_args=sampling_args)
    analysis.run()
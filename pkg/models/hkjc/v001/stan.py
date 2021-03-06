import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from hkjc.sqa import *
from pkg.analysis import ModelSpec, StanAnalysis

# get category and model_name from the file's path
category, model_name = os.path.dirname(os.path.realpath(__file__)).split("/")[-2:]

class NewSpec(ModelSpec):
    """
    1. Implement `build_data`
    2. Make default args for `single_params`, `param_pairs`, `param_groups`
    """
    def __init__(self, category, model_name, 
                 single_params=[],
                 param_pairs=[], 
                 param_groups={}):
        super(NewSpec, self).__init__(category, model_name,
                                      single_params=single_params,
                                      param_pairs=param_pairs,
                                      param_groups=param_groups)

    def build_data(self):
        """
        - Select a subset of races
        - Map the horse ids to 1-based integer keys
        - 
        """
        data = {}
        sd = "20130101"
        df = results_df(Result.id > sd)
        horses = sorted(list(df["horse_id"].unique()))
        horses_idx = dict(zip(horses, range(1, len(horses) + 1)))
        N_horses = len(horses_idx)
        df["horse_stan_idx"] = df["horse_id"].map(lambda v: horses_idx[v])
        r_12 = df.loc[12]
        r_14 = df.loc[14]

        # number of races
        N_12_races = len(r_12.index.get_level_values(0).unique())
        N_14_races = len(r_14.index.get_level_values(0).unique())

        # horse indexes
        horse_index_12 = np.zeros((N_12_races, 12), dtype=int)
        horse_index_14 = np.zeros((N_14_races, 14), dtype=int)
        for i, (name, group) in enumerate(r_12.groupby(r_12.index.get_level_values(0))):
            horse_index_12[i, :] = group["horse_stan_idx"].values
        for i, (name, group) in enumerate(r_14.groupby(r_14.index.get_level_values(0))):
            horse_index_14[i, :] = group["horse_stan_idx"].values
        assert np.min(np.min(horse_index_12)) > 0
        assert np.min(np.min(horse_index_14)) > 0

        # horse race numbers for age adj factor
        nth_race_12 = np.zeros((N_12_races, 12), dtype=int)
        nth_race_14 = np.zeros((N_14_races, 14), dtype=int)
        for i, (name, group) in enumerate(r_12.groupby(r_12.index.get_level_values(0))):
            nth_race_12[i, :] = group["horse_race_num"].values
        for i, (name, group) in enumerate(r_14.groupby(r_14.index.get_level_values(0))):
            nth_race_14[i, :] = group["horse_race_num"].values
        assert np.min(np.min(nth_race_12)) > 0
        assert np.min(np.min(nth_race_14)) > 0

        # race winners
        winner_12 = r_12.groupby(r_12.index.get_level_values(0)).apply(lambda g: np.argmin(g["rank"].values) + 1).values
        winner_14 = r_14.groupby(r_14.index.get_level_values(0)).apply(lambda g: np.argmin(g["rank"].values) + 1).values

        data["N_horses"] = N_horses
        data["N_12_races"] = N_12_races
        data["N_14_races"] = N_14_races
        data["horse_index_12"] = horse_index_12
        data["horse_index_14"] = horse_index_14
        data["nth_race_12"] = nth_race_12
        data["nth_race_14"] = nth_race_14
        data["winner_12"] = winner_12
        data["winner_14"] = winner_14
        self.data = data

    def set_dimensions(self):
        # reporting
        print "N_horses:", self.data["N_horses"]
        print "N_12_races:", self.data["N_12_races"]
        print "N_14_races:", self.data["N_14_races"]

    def set_hyperparameters(self):
        pass

    def add_supplemental_plotters(self):
        """
        Create list of functions with arg signature: (fit, output_dir) for custom plots
        """
        def plot_age_curve_params(fit, output_dir):
            df = pd.DateFrame(fit.extract(permuted=True)["beta_age_curve"], 
                              columns=["Race_Num_Adj_%d" % i for i in range(3)])
            fig = sns.pairplot(df, vars=list(df.columns), 
                               diag_kind="kde", plot_kws={"alpha": 0.1})
            fn = os.path.join(output_dir, "age_curve_args.png")
            print "writing < %s >" % fn
            fig.savefig(fn, bbox_inches="tight")

        self.supplemental_plot_funcs.append(plot_age_curve_params)


def main():
    model_spec = NewSpec(category, model_name)
    # adjust inference settings as needed
    sampling_args = {}
    analysis = StanAnalysis(model_spec, sampling_args=sampling_args)
    analysis.run()


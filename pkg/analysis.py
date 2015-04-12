import os
import traceback
import numpy as np
import pandas as pd
import pystan
import seaborn as sns
import matplotlib.pyplot as plt

from .dag import parse_stan
from . import conf

class ModelSpec(object):
    """
    Logic for a Stan model:
     - the Stan code
     - possibly a dictionary of Stan-data, `data`
     - method to build the data Stan needs
     - parameters we want to analyze / visualize
    """
    def __init__(self, category, model_name, single_params=[], param_pairs=[], param_groups={}):
        self.category = category
        self.model_name = model_name
        self.single_params = single_params
        self.param_pairs = param_pairs
        self.param_groups = param_groups

        code_fn = os.path.join(conf.models_dir, self.category, self.model_name, "model.stan")
        self.model_code = open(code_fn).read()
        self.build_data()

    def build_data(self):
        raw_input("-->")
        raise NotImplementedError("ModelSpec.build_data: must override in subclass of ModelSpec.")


class StanAnalysis(object):
    """
    Logic for running an analysis given a ModelSpec and inference parameters.
    """
    def __init__(self, model_spec, sampling_args={}, clean_output=True):
        self.model_spec = model_spec
        self.sampling_args = sampling_args
        self.output_dir = os.path.join(conf.static_dir, self.model_spec.category, self.model_spec.model_name)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        if clean_output:
            self.clean_output_dir()

    def __repr__(self):
        return "<StanAnalysis(category=%s, model_name=%s)>" % (self.model_spec.category, self.model_spec.model_name)

    def compile(self):
        print "compiling model ..."
        self.model = pystan.StanModel(model_code=self.model_spec.model_code)

    def sample(self):
        if not hasattr(self, "model"):
            self.compile()
        _iter = self.sampling_args.get("iter", 2000)
        chains = self.sampling_args.get("chains", 4)
        warmup = self.sampling_args.get("warmup", _iter // 2)
        thin = self.sampling_args.get("thin", 1)
        print "sampling posterior ..."
        print "  iter   =", _iter
        print "  chains =", chains
        print "  warmup =", warmup
        print "  thin   =", thin

        self.fit = self.model.sampling(data=self.model_spec.data,
                                      warmup=warmup,
                                      chains=chains,
                                      iter=_iter,
                                      thin=thin)

    def post_process(self, graphviz=True):
        """
        Plot parameters of interest in standard format and write text output.
        """
        print "post processing ..."
        for param in self.model_spec.single_params:
            self.single_param_plot(param)

        for pair in self.model_spec.param_pairs:
            self.param_pair_plot(pair)

        for name, params in self.model_spec.param_groups.items():
            self.param_group_plot(name, params)

        if graphviz:
            try:
                self.graphviz_plot()
            except:
                traceback.print_exc()

        self.write_fit_stats()
        self.copy_notes()

    def run(self):
        self.compile()
        self.sample()
        self.post_process()

    def single_param_plot(self, param, write_to_disk=True):
        """
        KDE + trace
        """
        print param
        trace = pd.Series(self.fit.extract(permuted=True)[param])
        fig, axs = plt.subplots(2, 1, figsize=(12, 8))
        sns.distplot(trace, 
                     kde_kws={"lw": 2.5},
                     hist_kws={"histtype": "stepfilled", "color": "slategray"},
                     ax=axs[0])
        x_min, x_max = axs[0].get_xlim()
        if x_min < 0. < x_max:
            axs[0].axvline(0., color="k", lw=1., alpha=0.6)
        trace.plot(ax=axs[1])
        fig.suptitle(param)
        if write_to_disk:
            fn = os.path.join(self.output_dir, "%s_trace.png" % param)
            print "writing < %s >" % fn
            fig.savefig(fn, bbox_inches="tight")
        else:
            plt.show()

    def param_pair_plot(self, pair, write_to_disk=True):
        """
        2d KDE to examine correlation
        """
        x = self.fit.extract(permuted=True)[pair[0]]
        y = self.fit.extract(permuted=True)[pair[1]]
        df = pd.DataFrame({pair[0]: x, pair[1]: y})
        sns.jointplot(pair[0], pair[1], data=df, kind="kde", size=10, space=0)
        fig = plt.gcf()
        if write_to_disk:
            fn = os.path.join(self.output_dir, "%s-%s.png" % pair)
            print "writing < %s >" % fn
            fig.savefig(fn, bbox_inches="tight")
        else:
            plt.show()

    def param_group_plot(self, name, params, write_to_disk=True):
        """
        Many parameter correlation plots at once, in less detail
        """
        df = pd.DataFrame({param: chain for param, chain in self.fit.extract(permuted=True).items() if param in params})
        fig = sns.pairplot(df, vars=list(df.columns))
        if write_to_disk:
            fn = os.path.join(self.output_dir, "%s_pairplot.png" % name)
            print "writing < %s >" % fn
            fig.savefig(fn, bbox_inches="tight")
        else:
            plt.show()

    def graphviz_plot(self):
        dag = parse_stan(self.model_spec.model_code, self.model_spec.model_name)
        fn = os.path.join(self.output_dir, "graphviz.png")
        print "writing < %s >" % fn
        dag.write_png(fn)

    def write_fit_stats(self):
        fit_stats_fn = os.path.join(self.output_dir, "fit_stats.txt")
        s = "<br>".join(repr(self.fit).replace(" ", "&nbsp;").split("\n")[1:])
        print "writing < %s >" % fit_stats_fn
        with open(fit_stats_fn, "w") as f:
            f.write(s)

    def copy_notes(self):
        notes_fn = os.path.join(conf.models_dir, self.model_spec.category, self.model_spec.model_name, "notes.txt")
        output_fn = os.path.join(self.output_dir, "notes.txt")
        if os.path.exists(notes_fn):
            with open(notes_fn, "r") as from_f:
                with open(output_fn, "w") as to_f:
                    to_f.write(from_f.read())

    def clean_output_dir(self):
        fns = [os.path.join(self.output_dir, fn) for fn in os.listdir(self.output_dir)]
        for fn in fns:
            os.remove(fn)
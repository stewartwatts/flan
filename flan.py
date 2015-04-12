import os
import pkg.conf as conf
from flask import Flask, render_template
app = Flask(__name__)

def get_category_dirs():
    category_dirs = [os.path.join(conf.static_dir, cat) for cat in os.listdir(conf.static_dir)]
    return [cd for cd in filter(os.path.isdir, category_dirs) if cd.split("/")[-1] not in ["css", "js"]]

def get_models(category_dir):
    model_dirs = [os.path.join(category_dir, model) for model in os.listdir(category_dir)]
    model_dirs = filter(os.path.isdir, model_dirs)
    return [model_dir.split("/")[-1] for model_dir in model_dirs]

def categorys():
    return [cat.split("/")[-1] for cat in get_category_dirs()]

@app.route("/")
def home():
    """navigate all models"""
    # tuples of (category, models list)
    cat_model_tups = []
    for category_dir in get_category_dirs():
        cat_model_tups.append((category_dir.split("/")[-1], get_models(category_dir)))
    kw = {
        "cat_model_tups": cat_model_tups, 
        "categorys": categorys(),
    }
    return render_template("home.html", **kw)

@app.route("/<category>")
def category_page(category):
    """models within a single category"""
    kw = {
        "cat_model_tups": [(category, get_models(os.path.join(conf.static_dir, category)))],
        "categorys": categorys(),
    }
    return render_template("home.html", **kw)

@app.route("/<category>/<model_name>/")
def model_page(category, model_name):
    """aggregate the outputs from this model's analysis"""
    model_dir = os.path.join(conf.static_dir, category, model_name)
    kw = {"categorys": categorys(), "category": category, "model_name": model_name,}

    # short-circuit if no model exists
    no_model = not os.path.exists(model_dir)
    if no_model:
        kw["no_model"] = no_model
        return render_template("model.html", **kw)

    # notes and fit print
    notes_fn = os.path.join(model_dir, "notes.txt")
    fit_print_fn = os.path.join(model_dir, "fit_stats.txt")
    if os.path.exists(notes_fn):
        with open(notes_fn, "r") as f:
            kw["notes"] = f.read()
    else:
        kw["notes"] = "No model notes."
    if os.path.exists(fit_print_fn):
        with open(fit_print_fn, "r") as f:
            kw["fit_stats"] = f.read()
    else:
        kw["fit_stats"] = "No model fit stats."

    # graphviz
    if os.path.join(model_dir, "graphviz.png"):
        kw["has_graphviz"] = True

    # filter for filenames of each plot type to make list of static urls
    fns = os.listdir(model_dir)
    single_param_fns = [fn for fn in fns if "trace" in fn]
    param_pair_fns = [fn for fn in fns if "-" in fn]
    param_group_fns = [fn for fn in fns if "pairplot" in fn]
    # format filenames into (title, fn)
    kw["single_params"] = [(fn.replace("_trace.png", ""), fn) for fn in single_param_fns]
    kw["param_pairs"] = [("%s vs %s" % tuple(fn.replace(".png", "").split("-")[::-1]), fn) for fn in param_pair_fns]
    kw["param_groups"] = [(fn.replace("_pairplot.png", ""), fn) for fn in param_group_fns]

    return render_template("model.html", **kw)

if __name__ == "__main__":
    app.run()
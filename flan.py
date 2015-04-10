import os
import pkg.conf as conf
from flask import Flask, render_template
app = Flask(__name__)

def get_category_dirs():
    category_dirs = [os.path.join(conf.static_dir, cat) for cat in os.listdir(conf.static_dir)]
    return filter(os.path.isdir, category_dirs)

def get_models(category_dir):
    model_dirs = [os.path.join(category_dir, model) for model in os.listdir(category_dir)]
    model_dirs = filter(os.path.isdir, model_dirs)
    return [model_dir.split("/")[-1] for model_dir in model_dirs]

@app.route("/")
def home():
    """navigate all models"""
    category_dirs = get_category_dirs()
    # tuples of (category, models list)
    cat_model_tups = []
    for category_dir in category_dirs:
        cat_model_tups.append(category_dir.split("/")[-1], get_models(category_dir))
    return render_template("home.html", cat_model_tups)

@app.route("/<category>")
def category_page(category):
    """models within a single category"""
    category_dir = os.path.join(conf.static_dir, category)
    models = [model for model in os.listdir(category_dir) if os.isdir(os.path.join(category_dir, model))]
    kw = dict(category=category, models=models)
    return render_template("category.html", **kw)

@app.route("/tag/<tag_name>")
def tagged_page(tag_name):
    """models with `tag_name` in their 'tags.txt' file"""
    return render_template("category.html", **kw)

@app.route("/<category>/<model_name>/")
def model_page(category, model_name):
    """aggregate the outputs from this model's analysis"""
    model_dir = os.path.join(conf.static_dir, category, model_name)
    kw = {
        "category": category, 
        "model_name": model_name,
    }
    with open(os.path.join(model_dir, "fit_stats.txt")) as f:
        kw["fit_stats"] = f.read()
    return render_template("model.html", **kw)

if __name__ == "__main__":
    app.run()
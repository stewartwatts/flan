import os

pkg_dir = os.path.dirname(os.path.realpath(__file__))
flan_dir = os.path.abspath(os.path.join(pkg_dir, os.pardir))

models_dir = os.path.join(pkg_dir, "models")
static_dir = os.path.join(flan_dir, "static")

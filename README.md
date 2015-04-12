### Flan
-----
Flan is intended to streamline the bookkeeping involved in building up Stan models iteratively using PyStan.

#### Creating a new model
 - create a submodule in `pkg/models/<category>/<model_name>/`
 - drop your Stan model definition into `model.stan`
 - write a Python class inheriting from `pkg.analysis.ModelSpec`, that implements the `build_data` method, which should set an instance's `data` attribute to a dictionary containing the data payload required for PyStan's `StanModel.sampling` call
 - this class should also define default constructor arguments for the model parameters, pairs of parameters, or groups of parameters to visualize 
 - optionally, write a `notes.txt` file in the model module directory to describe the goals of the model or takeaways from examining the results

#### Running an analysis
 - the constructor for class `pkg.analysis.StanAnalysis` takes an instance of the ModelSpec subclass described above and optionally some sampling parameters
 - StanAnalysis implements some parameter plotting methods for convenience, and drops the output into a directory of the format `static/<category>/<model_name>`
 - `runner.py` imports one or more model submodules and runs the analyses
 
#### Interacting with outputs
 - use Flask to interact with the outputs of various models
 - `$ python flan.py   # starts Flask to serve model outputs to a web browser`
 - go to `http://127.0.0.1:5000/` or wherever Flask indicates it is serving

#### Graphviz
 - A *very* rough, untested attempt is made to parse Stan model definitions into Graphviz Dot graphs. 
 - Dot cannot draw overlapping plates, so instead plates correspond to Stan's indexing of a datatype.  For example, to model `i` students answering `j` question, with the answers indexed by `[i, j]`, there will be a plate for the `i` students, the `j` questions, and the `[i, j]` answers, instead of two overlapping plates that share the answers.
 - Graphviz is not Python software, so it must be pre-installed with a non-pip package manager, like apt-get.

#### Dependencies
 - Apart from Graphviz, the other dependencies listed in requirements.txt are all easily installed with pip.
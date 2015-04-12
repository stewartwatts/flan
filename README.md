### Flan
-----
Flan is intended to streamline the bookkeeping involved in building up Stan models iteratively using PyStan.

#### Creating a new model
 - create a submodule in `pkg/models/<category>/<model_name>/`
 - drop your Stan model definition into `model.stan`
 - writing a Python class inheriting from `pkg.analysis.ModelSpec`, that implements the `build_data` method, which should set an instance's `data` attribute to a dictionary containing the data payload required for PyStan's `StanModel.sampling` call
 - this class should also define default constructor arguments for which model parameters we will want to visualize for a close examination, or pairs of parameters to plot together, or a group of parameters to visualize together
 - optionally, write a `notes.txt` file in the model module directory to describe the goals of the model or takeaways from examinging the results

#### Running an analysis
 - the constructor for class `pkg.analysis.StanAnalysis` takes an instance of the ModelSpec subclass described above and optionally some sampling parameters
 - StanAnalysis implements some general plotting methods for convenience, and drops the output into a directory of the format `static/<category>/<model_name>`
 - `runner.py` imports one or more model submodules and runs the analyses
 
#### Interacting with outputs
 - use Flask to interact with the outputs of various models
 - `$ python flan.py   # starts Flask to serve your model outputs to your browser`
 - go to `http://127.0.0.1:5000/` or wherever Flask says it is serving on your machine to navigate through your models and view their outputs
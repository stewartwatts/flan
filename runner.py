from pkg.models.example.eight_schools_001.stan import main as es1
# import other models ...

models = [
    es1, 
]

if __name__ == "__main__":
    for model_f in models:
        model_f()
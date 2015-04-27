from pkg.models.hkjc.v001.stan import main as hkjc001
# import other models ...

models = [
    hkjc001, 
]

if __name__ == "__main__":
    for model in models:
        model()

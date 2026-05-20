class Stock:
    def __init__(self, nom, quantite):
        self.nom = nom
        self.quantite = quantite
    def get_Stock(self):
        return self.quantite
    def stock_update(self, update):
        self.quantite += update

class Process:
    def __init__(self, nom, needs, results, delay):
        self.nom = nom
        self.needs = needs
        self.results = results
        self.delay = delay
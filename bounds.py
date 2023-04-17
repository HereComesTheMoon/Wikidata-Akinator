import abc
from math import log10
from itertools import chain
from utilities import SPARQL, id_to_label, LENGTH_ID_PREFIX
from random import choice


class Bound(abc.ABC):
    @abc.abstractmethod
    def get(self) -> str:
        pass

    @abc.abstractmethod
    def format(self, question: str) -> str:
        pass

    @abc.abstractmethod
    def update(self, question: str, answer: bool):
        pass

    @abc.abstractmethod
    def next_question(self, constraints: str):
        pass


class BoundTrivial(Bound):
    def __init__(self):
        self.wrong_guesses = []
        self.last_guess = None

    def get(self) -> str:
        if not self.wrong_guesses:
            return ""
        return "FILTER( ?country NOT IN ( wd:" + ",wd:".join(self.wrong_guesses) + ") )\n"

    def format(self, country: str) -> str:
        return f"Is your country {country} ({id_to_label(country)})?"

    def update(self, question: str, answer: bool):
        assert self.last_guess is not None
        assert not answer
        self.wrong_guesses.append(self.last_guess)
        self.last_guess = None

    def next_question(self, constraints: str) -> str:
        query = """SELECT DISTINCT ?country WHERE {\n?country wdt:P31 wd:Q6256 .\n"""
        query += constraints + "\n}"
        SPARQL.setQuery(query)
        ret = SPARQL.queryAndConvert()['results']['bindings']
        countries_left = [row["country"]["value"][LENGTH_ID_PREFIX:] for row in ret]
        res = choice(countries_left)
        self.last_guess = res
        return self.format(res)


class BoundPopulation(Bound):
    population = "wd:Q1082"

    def __init__(self):
        self.l = None
        self.r = None
        self.next_value = None

    def get(self) -> str:
        s = "?country wdt:P1082 ?pop .\n"
        if not self.l and not self.r:
            return s
        elif not self.r:
            return s + f"FILTER({self.l} <= ?pop)"
        elif not self.l:
            return s + f"FILTER(?pop < {self.r})"
        else:
            return s + f"FILTER({self.l} <= ?pop && ?pop <= {self.r})"

    def format(self, question: str) -> str:
        return f"Is the population of your country greater than {question:,}?"

    def update(self, question: str, answer: bool):
        assert self.next_value is not None
        if answer:
            self.l = self.next_value
        else:
            self.r = self.next_value
        self.next_value = None

    def next_question(self, constraints: str) -> str:
        query = """
            SELECT DISTINCT (AVG (?pop) AS ?result)
            WHERE {
              ?country wdt:P31 wd:Q6256 .
        """
        query += constraints + "\n}"
        SPARQL.setQuery(query)
        ret = SPARQL.queryAndConvert()
        val = float(ret["results"]["bindings"][0]["result"]["value"])
        length = int(log10(val)) - 2
        val = int((val // pow(10, length)) * pow(10, length))
        assert self.next_value is None
        self.next_value = val
        return self.format(val)
        

class BoundNearWater(Bound):
    near_water = "wdt:P206"
    def __init__(self):
        self.near = []
        self.not_near = []
        self.last_guess = None

    def get(self) -> str:
        return "\n".join(f"?country {self.near_water} wd:{water} ." for water in self.near) \
            + "\n" \
            + "\n".join(f"MINUS {{ ?country {self.near_water} wd:{water} . }}" for water in self.not_near) \
            + "\n"
        
    def format(self, question: str) -> str:
        return f"Is your country located in or next to the following body of water? — {question} ({id_to_label(question)})"

    def update(self, question: str, answer: bool):
        assert self.last_guess is not None
        if answer:
            self.near.append(self.last_guess)
        else:
            self.not_near.append(self.last_guess)
        self.last_guess = None

    def next_question(self, constraints: str) -> str:
        query = """SELECT DISTINCT ?water (COUNT(DISTINCT ?country) AS ?number) WHERE {
            ?country wdt:P31 wd:Q6256 .
            ?country wdt:P206 ?water .
        """
        query += constraints + "\nMINUS {\n" \
            + "\n".join(f"    ?water {self.near_water} wd:{water} ." for water in chain(self.near, self.not_near)) \
            + "\n} } GROUP BY ?water ORDER BY DESC(?number)\n"
        SPARQL.setQuery(query)
        ret = SPARQL.queryAndConvert()
        val = None
        res = [row["water"]["value"][LENGTH_ID_PREFIX:] for row in ret["results"]["bindings"]]
        for candidate in res:
            if candidate not in self.near and candidate not in self.not_near:
                val = candidate
                break
        if val is None:
            print("Oh no! I want to ask which body of water you are nearby, but there are no further candidates: I already know exactly which bodies of water you are close to. Handling this rare issue would make control flow vastly more complicated, so I will just abort.")
            assert False
        self.last_guess = val
        return self.format(val)


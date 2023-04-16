from SPARQLWrapper import SPARQLWrapper, JSON
from typing import NamedTuple
from pprint import pprint
from random import choice
import abc
from math import log10

USER_AGENT: str = "JustTestingForNow/0.0 (testing@protonmail.ch)"
LENGTH_ID_PREFIX: int = len("http://www.wikidata.org/entity/")

SPARQL = SPARQLWrapper( "https://query.wikidata.org/sparql" )
SPARQL.addCustomHttpHeader("User-Agent", USER_AGENT)
SPARQL.setReturnFormat(JSON)


class Country(NamedTuple):
    name: str
    id: str


def query_countries():
    sparql = SPARQLWrapper( "https://query.wikidata.org/sparql" )
    sparql.addCustomHttpHeader("User-Agent", USER_AGENT)
    sparql.setReturnFormat(JSON)
    query = """
        SELECT DISTINCT ?entity ?entityLabel WHERE {
            ?entity wdt:P31 wd:Q6256 . 
            ?article schema:about ?entity .
            ?article schema:isPartOf <https://en.wikipedia.org/>.
            FILTER NOT EXISTS {?entity wdt:P31 wd:Q3024240}
            FILTER NOT EXISTS {?entity wdt:P31 wd:Q28171280}
            OPTIONAL { ?entity wdt:P576 ?dissolved } .
            FILTER (!BOUND(?dissolved)) 
            SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
        }
        ORDER BY ?entityLabel
    """
    sparql.setQuery(query)
    ret = sparql.queryAndConvert()
    for val in ret["results"]["bindings"]:
        yield Country(
            val["entityLabel"]["value"],
            val["entity"]["value"][LENGTH_ID_PREFIX:]
        )


# def query_properties(props: list[str]):
#     sparql = SPARQLWrapper( "https://query.wikidata.org/sparql" )
#     sparql.addCustomHttpHeader("User-Agent", USER_AGENT)
#     sparql.setReturnFormat(JSON)
#     query = """
#     SELECT DISTINCT ?property (COUNT (?obj) AS ?occurrences)
#     WHERE { 
#         ?obj ?property ?value .
#     }
#     GROUP BY ?property
#     """
#     sparql.setQuery(query)
#     ret = sparql.queryAndConvert()
#     for val in ret["results"]["bindings"]:
#         yield Country(
#             val["entityLabel"]["value"],
#             val["entity"]["value"][LENGTH_ID_PREFIX:]
#         )

def id_to_label(id: str) -> str:
    query = f"""
        SELECT  *
        WHERE {{
                wd:{id} rdfs:label ?label .
                FILTER (langMatches( lang(?label), "EN" ) )
              }} 
        LIMIT 1
    """
    SPARQL.setQuery(query)
    try:
        return SPARQL.queryAndConvert()['results']['bindings'][0]['label']['value']
    except:
        print(f"Could not fetch label of wd:{id} from Wikidata.")
        return id

class Akinator:
    def __init__(self):
        self.turns = 0
        self.query_head = """SELECT DISTINCT ?country ?pop
        WHERE {
          ?country wdt:P31 wd:Q6256 .
        """
        self.query_blocks = [
            BoundTrivial(),
            BoundPopulation(),
        ]
        self.query_tail = """}"""
        self.countries_left = float('inf')

    def turn(self):
        self.turns += 1
        constraints = self.get_constraints()
        self.candidates()
        
        bound = choice(self.query_blocks)
        question = bound.next_question(constraints)
        answer = self.ask_question(question)
        bound.update(question, answer)

    def get_constraints(self) -> str:
        return "\n".join(map(lambda block: block.get(), self.query_blocks))

    def candidates(self) -> list:
        query = """SELECT DISTINCT ?country WHERE { ?country wdt:P31 wd:Q6256 .\n"""
        query += self.get_constraints() + "\n}"
        SPARQL.setQuery(query)
        ret = SPARQL.queryAndConvert()['results']['bindings']
        res = [row["country"]["value"] for row in ret]
        assert len(res) <= self.countries_left
        self.countries_left = len(res)
        return res

        return 

    # def pick_question(self, bound) -> str:
    #     query = bound.query_head + "\n".join(map(lambda block: block.get(), self.query_blocks)) + self.query_tail
    #     print()
    #     print()
    #     print(query)
    #     print()
    #     print()
    #     SPARQL.setQuery(query)
    #     ret = SPARQL.queryAndConvert()
    #     pprint(ret)
    #     pprint(ret["results"]["bindings"])

    def ask_question(self, question: str) -> bool:
        print(f"QUESTION {self.turns}! {self.countries_left} countries are left. \n\n{question}\n")
        while True:
            choice = input("Y/N?").lower()
            match choice:
                case 'yes' | 'y':
                    return True
                case 'no' | 'n':
                    return False


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
        return f"Is your country {country}?"

    def update(self, question: str, answer: bool):
        assert self.last_guess is not None
        assert not answer
        self.wrong_guesses.append(self.last_guess)
        self.last_guess = None
    
    def next_question(self, constraints: str) -> str:
        query = """SELECT DISTINCT ?country WHERE { ?country wdt:P31 wd:Q6256 .\n"""
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
        match (self.l, self.r):
            case None, None:
                return s
            case _, None:
                return s + f"FILTER({self.l} <= ?pop)"
            case None, _:
                return s + f"FILTER(?pop < {self.r})"
            case _, _:
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
    

    # def turn(self, query_blocks: list):
    #     SPARQL.resetQuery()
    #     query = self.query_head + "\n".join(map(lambda block: block.get(), query_blocks)) + self.query_tail
    #     SPARQL.setQuery(query)
    #     ret = SPARQL.queryAndConvert()
    #     pprint(ret)
    #     ret["results"]["bindings"]
        
# class BoundNearWater(Bound):
#     near_water = "wdt:P206"
#     def __init__(self):
#         self.near = []
#         self.not_near = []

#     def get(self) -> str:
#         return "\n".join(f"?country {self.near_water} {water} ." for water in self.near) \
#             + "\n MINUS {\n" \
#             + "\n".join(f"?country {self.near_water} {water} ." for water in self.not_near)
        
#     def format(self, question: str) -> str:
#         return f"Is your country located in or next to the following body of water? — {question}"

#     def update(self, question: str, answer: bool):
#         if answer:
#             self.near.append(question)
#         else:
#             self.not_near.append(question)

#     def next_question(self, constraints: str) -> str:
#         query = """SELECT DISTINCT ?water (COUNT(DISTINCT ?country AS ?number)) WHERE {
#             ?country wdt:P31 wd:Q6256 .
#             ?country wdt:P206 ?water .
#         """
#         query += constraints + "\nMINUS {" + "\n".join(f"?water = {water} ." for water in zip(self.not_near, self.near)) + "} } GROUP BY ?water ORDER BY DESC(?number) LIMIT 1"
#         return query
    
def query_properties(props: list[str]):
    sparql = SPARQLWrapper( "https://query.wikidata.org/sparql" )
    sparql.addCustomHttpHeader("User-Agent", USER_AGENT)
    sparql.setReturnFormat(JSON)
    query = """
    SELECT DISTINCT ?property (COUNT (?obj) AS ?occurrences)
    WHERE { 
        ?obj ?property ?value .
    }
    GROUP BY ?property
    """
    sparql.setQuery(query)
    ret = sparql.queryAndConvert()
    for val in ret["results"]["bindings"]:
        yield Country(
            val["entityLabel"]["value"],
            val["entity"]["value"][LENGTH_ID_PREFIX:]
        )
    



if __name__ == '__main__':
    ak = Akinator()
    while True:
        ak.turn()

    # bw = BoundNearWater()
    # print(bw.next_question(""))
    # for x in query_countries():
    #     print(x)
    
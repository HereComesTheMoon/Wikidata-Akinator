from pprint import pprint
from random import choice
from bounds import BoundTrivial, BoundPopulation, BoundNearWater
from utilities import SPARQL


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
            BoundNearWater(),
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
        query = """SELECT DISTINCT ?country WHERE {\n?country wdt:P31 wd:Q6256 .\n"""
        query += self.get_constraints() + "\n}"
        SPARQL.setQuery(query)
        try:
            ret = SPARQL.queryAndConvert()['results']['bindings']
        except Exception as e:
            print(f"ERROR fetching candidates. Query: \n\n {query}\n\n\n")
            raise e
        res = [row["country"]["value"] for row in ret]
        assert len(res) <= self.countries_left
        self.countries_left = len(res)
        return res

    
    def ask_question(self, question: str) -> bool:
        print(f"QUESTION {self.turns}! {self.countries_left} countries are left. \n\n{question}\n")
        while True:
            choice = input("Y/N?").lower()
            if choice == 'yes' or choice == 'y':
                return True
            elif choice == 'no' or choice == 'n':
                return False


if __name__ == '__main__':
    ak = Akinator()
    while True:
        ak.turn()

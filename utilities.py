from SPARQLWrapper import SPARQLWrapper, JSON
from typing import NamedTuple

USER_AGENT: str = "JustTestingForNow/0.0 (testing@protonmail.ch)"
LENGTH_ID_PREFIX: int = len("http://www.wikidata.org/entity/")

SPARQL = SPARQLWrapper("https://query.wikidata.org/sparql")
SPARQL.addCustomHttpHeader("User-Agent", USER_AGENT)
SPARQL.setReturnFormat(JSON)


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

# Not used:

class Country(NamedTuple):
    name: str
    id: str


def query_countries():
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
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


def query_properties(props: list):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
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

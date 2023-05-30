# Wikidata-Akinator
## About
A proof-of-concept of an Akinator-like guessing game, in which the AI/program makes educated guesses to figure out which Wikidata item you are thinking of.
Cannot be played offline, since it queries Wikidata. To start, think of any existing country, then run ``main.py`` and answer``y`` or ``n`` as necessary.

## Implementation & Concept
At each step, the program queries Wikidata how many possible items exist, fulfilling all properties which we know about so far. If there is just one remaining, then we have found the solution.

For this the program asks a question each turn, and keeps track of the answers of the player. The answers are aggregated into a Wikidata query, which restricts the scope of remaining objects.

Ideally, the player could choose literally anything as their target item (assuming it has a Wikidata entry), and our program would automatically find a Y/N question which cuts the number of remaining candidates in half.

## Problems / Verdict
### Query Timeouts
The most severe issue encountered during development was that of query timeouts. Essentially, Wikidata only allocates a set amount of time to execute each query, and will return a timeout error if it does not complete in time.

When exactly timeouts occur is difficult to predict: In particular, even if a specific query executes just fine, adding an additional restriction/filter the query may cause it to time out.

Generally, the problem can be prevented by restricting ourselves to a very small subset of possible items, which is obviously unsatisfying.

### Finding Questions
Generating questions is a hard problem. A look at Wikidata entries, eg. [Shunting-yard Algorithm](https://www.wikidata.org/wiki/Q1199602) or [Germany](https://www.wikidata.org/wiki/Q183) makes it clear that it'd be difficult to automatically generate questions capable of narrowing down the space of solutions.

Querying the remaining items to figure out a property which as many as possible (but no more than half) of them share quickly results in timeouts as long as there are too many possible items.

Furthermore, work needs to be done to handle numerical values or dates. Questions such as "Was this item released before DD/MM/YYY?" have to be handled differently from questions such as "Does this item have the property X?"

### Building Queries
Incredibly fiddly. This was handled by string concatenation, and requires a lot of care. The library ecosystem for SparQL is much less rich than for SQL.


"""Hand-labelled synthetic cases. These are not model-generated transcripts."""


def recipe(title, ingredients, **fields):
    return dict(title=title, ingredients=ingredients, diet="Vegan", minutes=15,
                protein_g=12, instructions=["Cook and serve."], **fields)


def variant(title, ingredients, **fields):
    row = recipe(title, ingredients)
    row.update(fields)
    return row


def case(name, recipes, expected, constraints=None, pantry=None, **extra):
    return dict(name=name, recipes=recipes, expected=expected,
                constraints=constraints or {},
                pantry=pantry if pantry is not None else [{"Ingredient": "Rice", "Quantity": 1, "Unit": "cup"}],
                **extra)


CASES = [
    case("vegan rejects meat and dairy despite labels", [recipe("Chicken", ["Chicken"]), recipe("Milk", ["Milk"]), recipe("Rice", ["Rice"])], ["Rice"], {"diet": "Vegan"}),
    case("vegetarian permits dairy but rejects fish", [variant("Yogurt", ["Yogurt"], diet="Vegetarian"), recipe("Fish", ["Fish"])], ["Yogurt"], {"diet": "Vegetarian"}),
    case("time boundary and unknown time", [variant("Slow", ["Rice"], minutes=21), variant("Unknown", ["Rice"], minutes=None), variant("Boundary", ["Rice"], minutes=20)], ["Boundary"], {"max_minutes": 20}),
    case("avoid ingredient case insensitive", [recipe("Peanut", ["Peanut butter"]), recipe("Rice", ["Rice"])], ["Rice"], {"avoid": ["PEANUT"]}),
    case("pantry overlap beats response order", [recipe("Shop", ["Rice", "Tofu", "Lemon", "Ginger"]), recipe("Almost", ["Rice", "Lemon"]), recipe("Cook", ["Rice"])], ["Cook", "Almost", "Shop"], statuses=["Cook now", "Almost ready", "Needs shopping"], scores=[100, 50, 25]),
    case("normalizes pantry case and whitespace", [recipe("Rice", [" rice "])], ["Rice"], pantry=[{"Ingredient": " RICE ", "Quantity": 1}], scores=[100]),
    case("fastest priority", [variant("Slow", ["Rice"], minutes=20), variant("Fast", ["Rice", "Lemon"], minutes=5)], ["Fast", "Slow"], {"priority": "Fastest"}),
    case("protein priority", [variant("Low", ["Rice"], protein_g=5), variant("High", ["Rice", "Tofu"], protein_g=30)], ["High", "Low"], {"priority": "Highest protein"}),
    case("fewest missing priority", [recipe("Missing", ["Rice", "Lemon"]), recipe("Present", ["Rice"])], ["Present", "Missing"], {"priority": "Fewest missing ingredients"}),
    case("high protein breaks overlap ties", [variant("Low", ["Rice"], protein_g=5), variant("High", ["Rice"], protein_g=30)], ["High", "Low"], {"high_protein": True}),
    case("eggplant is not egg", [recipe("Eggplant", ["Eggplant"])], ["Eggplant"], {"diet": "Vegan"}),
    case("empty ingredient list needs shopping", [recipe("Unknown", [])], ["Unknown"], statuses=["Needs shopping"], scores=[0]),
    case("duplicate ingredients rejected", [recipe("Duplicate", ["Rice", "rice"])], [], parse_ok=False),
    case("valid empty response", [], []),
    case("zero stock must not count as available", [recipe("Rice", ["Rice"])], ["Rice"], pantry=[{"Ingredient": "Rice", "Quantity": 0}], statuses=["Almost ready"], scores=[0], known_gap=True),
    case("singular plural pantry alias", [recipe("Chickpeas", ["Chickpea"])], ["Chickpeas"], pantry=[{"Ingredient": "Chickpeas", "Quantity": 1}], scores=[100], known_gap=True),
    case("unlisted meat term duck", [recipe("Duck", ["Duck"])], [], {"diet": "Vegetarian"}, known_gap=True),
    case("unlisted dairy term feta", [recipe("Feta", ["Feta"])], [], {"diet": "Vegan"}, known_gap=True),
    case("avoid synonym groundnut", [recipe("Groundnut", ["Groundnut oil"])], [], {"avoid": ["peanut"]}, known_gap=True),
]

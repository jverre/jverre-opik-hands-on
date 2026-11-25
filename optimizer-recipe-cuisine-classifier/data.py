"""Labeled recipe blurbs for the cuisine classifier.

Thirty short, invented menu descriptions across five cuisines. Each blurb
describes a dish by technique and ingredients rather than naming the
cuisine, and a few are deliberately tricky (a peanut stew that is not
Sichuan, a chili-oil dish that is not Oaxacan) so a vague prompt has to
guess. The first four per cuisine are the training set the optimizer
climbs against; the last two per cuisine are held out to check the gain.
"""

CUISINES = ["levantine", "oaxacan", "sichuan", "nordic", "west-african"]

# (description, label), grouped by cuisine; the last two of each group are held out.
_ITEMS: list[tuple[str, str]] = [
    # --- levantine ---
    ("Smoke-blistered eggplant whipped with tahini, lemon and garlic, scooped up "
     "with warm flatbread and crowned with pomegranate seeds.", "levantine"),
    ("Crisp bulgur shells stuffed with spiced minced lamb and pine nuts, served "
     "with a cool mint-yogurt dip.", "levantine"),
    ("Chickpea and parsley fritters scented with cumin, tucked into pita with "
     "pickled turnip and a ribbon of tahini sauce.", "levantine"),
    ("Lamb shoulder slow-roasted with cinnamon and allspice, packed with rice, "
     "almonds and raisins, carved at the table.", "levantine"),
    ("Tender lamb slow-cooked over rice with allspice and cinnamon, finished "
     "with toasted almonds and warm yogurt.", "levantine"),
    ("Thyme-and-sesame flatbread baked until blistered and brushed with olive "
     "oil, torn and eaten with labneh.", "levantine"),
    # --- oaxacan ---
    ("A dark sauce of toasted chiles, chocolate and ground seeds, ladled over "
     "poached chicken with rice.", "oaxacan"),
    ("Fried plantain turnovers filled with black bean paste and dusted with "
     "crumbly aged cheese.", "oaxacan"),
    ("Grasshoppers toasted with garlic, lime and chile, piled onto a fresh "
     "tortilla with avocado.", "oaxacan"),
    ("Masa steamed in a banana leaf around chicken and a golden, cumin-tinged "
     "mole.", "oaxacan"),
    ("A frothy cold drink of ground toasted corn, cacao and cinnamon whisked "
     "until a pale foam rises.", "oaxacan"),
    ("Stringy fresh cheese folded into a quesadilla with squash blossoms and "
     "pungent herbs, griddled over a clay comal.", "oaxacan"),
    # --- sichuan ---
    ("Silken tofu simmered in a fiery chili-bean sauce with minced beef, "
     "finished with a numbing dusting of ground peppercorn.", "sichuan"),
    ("Chicken diced and stir-fried with a mountain of dried chilies and "
     "peanuts, tingling from toasted prickly ash.", "sichuan"),
    ("Wheat noodles tossed in sesame paste, chili oil and vinegar, topped with "
     "seasoned minced pork and preserved greens.", "sichuan"),
    ("Green beans blistered in a hot wok with minced pork, preserved mustard "
     "greens and a few dried chilies.", "sichuan"),
    ("Pork belly boiled, sliced thin and stir-fried twice with leeks and "
     "fermented broad bean paste.", "sichuan"),
    ("Silky eggplant strips braised until soft in a sweet, sour and spicy "
     "sauce redolent of garlic and pickled chili.", "sichuan"),
    # --- nordic ---
    ("Salt-and-sugar cured salmon sliced paper-thin with dill and a sweet "
     "mustard sauce, laid over dark rye.", "nordic"),
    ("Tiny meatballs in a cream gravy, served with boiled potatoes, pickled "
     "cucumber and tart lingonberry jam.", "nordic"),
    ("Thin slices of cured lamb draped over buttered flatbread with pickled "
     "beet and juniper-scented onions.", "nordic"),
    ("Barley porridge finished with browned butter and a spoonful of "
     "cloudberries.", "nordic"),
    ("Root vegetables roasted with juniper and caraway, drizzled with a "
     "soured cream and dill dressing.", "nordic"),
    ("Smoked trout flaked over a warm new-potato salad with horseradish, "
     "chives and a splash of cider vinegar.", "nordic"),
    # --- west-african ---
    ("Rice cooked in one pot in a smoky tomato and scotch bonnet base, served "
     "with sweet fried plantain.", "west-african"),
    ("Soft pounded yam with a thick okra and leafy green stew studded with "
     "smoked fish.", "west-african"),
    ("A rich peanut stew simmered with chicken, sweet potato and ginger, "
     "ladled over rice.", "west-african"),
    ("Smoky tomato and chile sauce pounded in a mortar with charred onion, "
     "spooned over boiled yam and fried fish.", "west-african"),
    ("Black-eyed pea batter whipped and fried into golden fritters, served "
     "with a fiery pepper sauce.", "west-african"),
    ("Spicy cassava dough steamed in leaves and served with a pepper-forward "
     "palm oil sauce and grilled mackerel.", "west-african"),
]

# Groups of six per cuisine: four for training, two held out.
TRAIN: list[tuple[str, str]] = []
HELD_OUT: list[tuple[str, str]] = []
for _i in range(0, len(_ITEMS), 6):
    TRAIN.extend(_ITEMS[_i : _i + 4])
    HELD_OUT.extend(_ITEMS[_i + 4 : _i + 6])

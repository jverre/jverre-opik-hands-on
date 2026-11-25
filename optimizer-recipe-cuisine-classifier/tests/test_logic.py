from types import SimpleNamespace

import classifier
import main
from data import CUISINES, HELD_OUT, TRAIN


def test_normalize_accepts_punctuation_and_spacing():
    assert classifier.normalize(" Sichuan. ") == "sichuan"
    assert classifier.normalize("West African") == "west-african"


def test_sentences_are_not_labels():
    assert classifier.is_correct("Nordic", "nordic")
    assert not classifier.is_correct("This dish belongs to Nordic cuisine.", "nordic")


def test_dataset_split_is_balanced_and_labeled():
    assert len(TRAIN) == 20 and len(HELD_OUT) == 10
    for split, per_cuisine in ((TRAIN, 4), (HELD_OUT, 2)):
        for cuisine in CUISINES:
            assert sum(label == cuisine for _, label in split) == per_cuisine
    assert not {t for t, _ in TRAIN} & {t for t, _ in HELD_OUT}


def test_metric_scores_exact_label_only():
    item = {"dish": "x", "label": "oaxacan"}
    assert main.cuisine_exact_match(item, "Oaxacan") == 1.0
    assert main.cuisine_exact_match(item, "Mexican") == 0.0


def test_trial_scores_flattens_rounds():
    history = [
        {"trials": [{"score": 0.4}, {"score": 1.0}]},
        {"trials": [{"score": 0.9}, {"score": None}]},
        {},
    ]
    assert main.trial_scores(history) == [0.4, 1.0, 0.9]


def test_to_mustache_rewrites_only_the_variable():
    out = main.to_mustache([{"role": "user", "content": "{dish}"}])
    assert out == [{"role": "user", "content": "{{dish}}"}]


def test_traced_function_runs_with_tracking_disabled(monkeypatch):
    """@opik.track and the OpenAI wrapper must not get in the way of unit tests."""
    answers = iter(["levantine", "Not sure", "sichuan"])

    def fake_create(**kwargs):
        message = SimpleNamespace(content=next(answers))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )
    monkeypatch.setattr(classifier, "_client", lambda: fake_client)

    items = [("a", "levantine"), ("b", "nordic"), ("c", "sichuan")]
    assert classifier.accuracy(items) == 2 / 3

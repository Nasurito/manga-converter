import pytest

import utils


@pytest.mark.parametrize("label, expected", [
    ("12", 12),
    ("271.5", 271.5),
    ("168.5 (VUS)", 168.5),
    ("Chapitre 3", 3),
    ("12.0", 12),
    ("pas de numéro", None),
])
def test_normalize_volume(label, expected):
    result = utils.normalize_volume(label)
    assert result == expected
    assert type(result) is type(expected)


@pytest.mark.parametrize("url, expected", [
    ("https://www.lelmanga.com/manga/one-piece", "lelmanga"),
    ("https://mangakatana.com/manga/kaiju-no-8.24869", "mangakatana"),
    ("http://sushiscan.fr/catalogue/test/", "sushiscan"),
    ("pas une url", None),
])
def test_get_domain(url, expected):
    assert utils.get_domain(url) == expected


class FakeDriver:
    """Navigateur factice : find_elements renvoie autant d'éléments que demandé."""
    def __init__(self, count):
        self.count = count

    def find_elements(self, by, selector):
        return [object()] * self.count


def test_wait_for_page_returns_without_prompt_when_ready(no_prompt):
    utils.wait_for_page(FakeDriver(count=5), "#readerarea img", min_count=2, timeout=1)


def test_wait_for_page_asks_user_after_timeout(monkeypatch):
    prompts = []
    monkeypatch.setattr("builtins.input", lambda message: prompts.append(message))

    utils.wait_for_page(FakeDriver(count=1), "#readerarea img", min_count=2, timeout=0)

    assert len(prompts) == 1


def test_wait_for_page_asks_user_without_selector(monkeypatch):
    prompts = []
    monkeypatch.setattr("builtins.input", lambda message: prompts.append(message))

    utils.wait_for_page(FakeDriver(count=5))

    assert len(prompts) == 1

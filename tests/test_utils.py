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


@pytest.mark.parametrize("name, expected", [
    ("Jujutsu Kaisen", "Jujutsu Kaisen"),
    ("Re:Zero / Arc 1?", "Re_Zero _ Arc 1_"),
    ('a<b>c"d|e*f\\g', "a_b_c_d_e_f_g"),
    ("Fin avec point...", "Fin avec point"),
    ("   ", "manga"),
])
def test_safe_filename(name, expected):
    assert utils.safe_filename(name) == expected


def test_wait_for_page_runs_prepare_page_until_ready(no_prompt):
    # prepare_page simule le passage en lecture verticale : la page affiche alors toutes les images
    driver = FakeDriver(count=1)
    calls = []
    def prepare(d):
        calls.append(d)
        d.count = 5

    utils.wait_for_page(driver, "#readerarea img", min_count=2, timeout=1, prepare_page=prepare)

    assert calls == [driver]


def test_wait_for_page_ignores_errors_while_page_is_loading(no_prompt):
    from selenium.common.exceptions import StaleElementReferenceException
    attempts = []
    def prepare(d):
        attempts.append(1)
        if len(attempts) == 1:
            raise StaleElementReferenceException("page en cours de rendu")
        d.count = 5

    utils.wait_for_page(FakeDriver(count=0), "#readerarea img", min_count=2, timeout=5, prepare_page=prepare)

    assert len(attempts) == 2


class FakeResponse:
    content = b"image"
    def raise_for_status(self):
        pass


class FlakySession:
    """Session qui échoue les `failures` premières fois."""
    def __init__(self, failures):
        self.failures, self.calls = failures, 0

    def get(self, url, timeout):
        self.calls += 1
        if self.calls <= self.failures:
            raise ConnectionError("coupure réseau")
        return FakeResponse()


def test_download_image_retries_then_succeeds(tmp_path, monkeypatch):
    monkeypatch.setattr(utils.time, "sleep", lambda seconds: None)
    session = FlakySession(failures=2)

    assert utils.download_image("https://img/1.jpg", str(tmp_path / "1.jpg"), session=session, attempts=3)
    assert session.calls == 3
    assert (tmp_path / "1.jpg").read_bytes() == b"image"


def test_download_image_gives_up_after_all_attempts(tmp_path, monkeypatch):
    monkeypatch.setattr(utils.time, "sleep", lambda seconds: None)
    session = FlakySession(failures=5)

    assert not utils.download_image("https://img/1.jpg", str(tmp_path / "1.jpg"), session=session, attempts=3)
    assert session.calls == 3

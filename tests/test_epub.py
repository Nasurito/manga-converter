import io
import os

from PIL import Image

from module.manga import prepare_epub_image


def save_image(path, size, image_format, mode="RGB"):
    Image.new(mode, size, "white").save(path, format=image_format)
    with open(path, "rb") as f:
        return f.read()


def test_landscape_page_is_rotated_without_touching_the_cache(tmp_path):
    path = tmp_path / "001.jpg"
    original = save_image(path, (300, 200), "JPEG")

    content = prepare_epub_image(str(path))

    with Image.open(io.BytesIO(content)) as page:
        assert page.format == "JPEG"
        assert page.size == (200, 300)  # tournée en portrait
    with open(path, "rb") as f:
        assert f.read() == original  # le fichier du cache est inchangé


def test_png_is_converted_to_jpeg_without_touching_the_cache(tmp_path):
    # Les images sont enregistrées en .jpg mais le site peut envoyer du PNG (ex: lelmanga)
    path = tmp_path / "002.jpg"
    original = save_image(path, (200, 300), "PNG", mode="RGBA")

    content = prepare_epub_image(str(path))

    with Image.open(io.BytesIO(content)) as page:
        assert page.format == "JPEG"
        assert page.mode == "RGB"
    with open(path, "rb") as f:
        assert f.read() == original


def test_portrait_jpeg_is_kept_as_is(tmp_path):
    path = tmp_path / "003.jpg"
    original = save_image(path, (200, 300), "JPEG")

    assert prepare_epub_image(str(path)) == original  # pas de recompression

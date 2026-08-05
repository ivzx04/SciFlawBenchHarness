import pytest
from core.registry import Registry

def test_register_and_create():
    reg: Registry[str] = Registry("thing")

    @reg.register("greeting")
    def make_greeting() -> str:
        return "hello"

    assert reg.create("greeting") == "hello"

def test_create_passes_kwargs_to_factory():
    reg: Registry[str] = Registry("thing")

    @reg.register("greeting")
    def make_greeting(name: str) -> str:
        return f"hello {name}"

    assert reg.create("greeting", name="joe") == "hello joe"

def test_duplicate_registration_raises():
    reg: Registry[str] = Registry("thing")
    reg.register("dup")(lambda: "first")

    with pytest.raises(ValueError, match="already registered"):
        reg.register("dup")(lambda: "second")

def test_get_unknown_name_raises():
    reg: Registry[str] = Registry("thing")
    with pytest.raises(KeyError):
        reg.get("nonexistent")

def test_create_unknown_name_raises():
    reg: Registry[str] = Registry("thing")
    with pytest.raises(KeyError):
        reg.create("nonexistent")

def test_names_returns_sorted():
    reg: Registry[str] = Registry("thing")
    reg.register("zebra")(lambda: "z")
    reg.register("apple")(lambda: "a")

    assert reg.names() == ["apple", "zebra"]

def test_register_returns_original_factory():
    reg: Registry[str] = Registry("thing")

    def make_greeting() -> str:
        return "hello"

    decorated = reg.register("greeting")(make_greeting)
    assert decorated is make_greeting

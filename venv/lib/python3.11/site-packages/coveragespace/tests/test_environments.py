# pylint: disable=missing-docstring,unused-variable,unused-argument,expression-not-assigned,singleton-comparison

from expecter import expect

from .. import environments


def describe_ci():
    def when_off_ci(monkeypatch):
        monkeypatch.delenv("APPVEYOR", raising=False)
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("CONTINUOUS_INTEGRATION", raising=False)
        monkeypatch.delenv("TRAVIS", raising=False)
        monkeypatch.delenv("DISABLE_COVERAGE", raising=False)

        expect(environments.ci()) == False

    def when_on_ci(monkeypatch):
        monkeypatch.setenv("TRAVIS", "true")

        expect(environments.ci()) == True

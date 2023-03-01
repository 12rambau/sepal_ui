"""
All the process that can be run using nox.

The nox run are build in isolated environment that will be stored in .nox. to force the venv update, remove the .nox/xxx folder.
"""

import nox


@nox.session(reuse_venv=True)
def lint(session):
    """Apply the pre-commits."""
    session.install("pre-commit")
    session.run("pre-commit", "run", "--a", *session.posargs)


@nox.session(reuse_venv=True)
def test(session):
    """Run all the test using the environment varialbe of the running machine."""
    session.install(".[test]")
    test_files = session.posargs or ["tests"]
    session.run("pytest", "--color=yes", "--cov", "--cov-report=html", *test_files)


@nox.session(reuse_venv=True)
def bin(session):
    """Run all the bin methods to validate the conda recipe."""
    session.install(".")
    session.run("module_deploy", "--help")
    session.run("module_factory", "--help")
    session.run("module_l10n", "--help")
    session.run("module_theme", "--help")
    session.run("module_venv", "--help")
    session.run("activate_venv", "--help")
    session.run("sepal_ipyvuetify", "--help")


@nox.session(reuse_venv=True)
def docs(session):
    """Build the documentation."""
    session.install(".[doc]")
    session.run("rm", "-rf", "docs/source/modules", external=True)
    session.run("rm", "-rf", "docs/build/html", external=True)
    session.run(
        "sphinx-apidoc",
        "--templatedir=docs/source/_templates/apidoc",
        "-o",
        "docs/source/modules",
        "sepal_ui",
    )
    session.run(
        "sphinx-build",
        "-v",
        "-b",
        "html",
        "docs/source",
        "docs/build/html",
        "-w",
        "warnings.txt",
    )
    session.run("python", "tests/check_warnings.py")


@nox.session(name="mypy", reuse_venv=True)
def mypy(session):
    """Run a mypy check of the lib."""
    session.install(".[dev]")
    test_files = session.posargs or ["sepal_ui"]
    session.run(
        "mypy",
        "--scripts-are-modules",
        "--ignore-missing-imports",
        "--install-types",
        "--non-interactive",
        "--disable-error-code",
        "func-returns-value",
        "--warn-redundant-casts",
        *test_files,
    )

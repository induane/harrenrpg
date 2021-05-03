from setuptools import setup, find_packages


setup(
    name="harren-rpg",
    version="0.0.1",
    description="Tales of Harren",
    author="Harren Press",
    author_email="harrenpress@gmail.com",
    keywords="game harren engine pygame",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=["log-color", "pygame", "six", "boltons", "pytoml"],
    entry_points={"console_scripts": ["harren = harren.entry_point:main"]},
    package_data={
        "harren": [
            "resources/*.*",
            "resources/**/*.*",
        ],
    },
)

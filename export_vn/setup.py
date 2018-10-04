from setuptools import setup, find_packages
setup(
    name="export_vn",
    version="0.1",
    packages=find_packages(),

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires=['docutils>=0.3'],

    package_data={
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst'],
        # And include any *.msg files found in the 'hello' package, too:
        'export_vn': ['*.msg'],
    },

    # metadata to display on PyPI
    author="Daniel Thonon",
    author_email="d.thonon9@gmail.com",
    description="",
    license="GPL",
)

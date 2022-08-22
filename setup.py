from setuptools import setup

def get_version(filename):
    """
    Get version from a file.

    Inspired by https://github.mabuchilab/QNET/.
    """
    with open(filename) as f:
        for line in f.readlines():
            if line.startswith("__version__"):
                return line.split("=")[1].strip()[1:-1]
    raise RuntimeError(
        "Could not get version from %s." % filename)


VERSION = get_version("treefarm/__init__.py")

with open('README.md') as f:
    long_description = f.read()

dev_requirements = [
    'codecov', 'flake8', 'pytest>=3.6', 'pytest-cov', 'twine', 'wheel',
    'sphinx', 'sphinx_rtd_theme']

setup(name="treefarm",
      version=VERSION,
      description="An extension of yt for creating merger-trees.",
      long_description=long_description,
      long_description_content_type='text/markdown',
      author="Britton Smith",
      author_email="brittonsmith@gmail.com",
      license="BSD 3-Clause",
      keywords=["simulation", "merger-tree", "astronomy", "astrophysics"],
      url="https://github.com/ytree-project/treefarm",
      project_urls={
          'Homepage': 'https://github.com/ytree-project/treefarm',
          'Documentation': 'https://treefarm.readthedocs.io/',
          'Source': 'https://github.com/ytree-project/treefarm',
          'Tracker': 'https://github.com/ytree-project/treefarm/issues'
      },
      packages=["treefarm"],
      include_package_data=True,
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "Intended Audience :: Science/Research",
          "Topic :: Scientific/Engineering :: Astronomy",
          "License :: OSI Approved :: BSD License",
          "Operating System :: MacOS :: MacOS X",
          "Operating System :: POSIX :: Linux",
          "Operating System :: Unix",
          "Natural Language :: English",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "Programming Language :: Python :: 3.9",
      ],
      install_requires=[
          'configparser',
          'h5py',
          'numpy',
          'yt>=3.4',
          'ytree'
      ],
      extras_require={
          'dev': dev_requirements,
          'rtd': [pkg for pkg in dev_requirements if 'sphinx' not in pkg],
      },
      python_requires='>=3.7'
)

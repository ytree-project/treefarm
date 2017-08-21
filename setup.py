from setuptools import setup

setup(name="ytree",
      version="2.0.1.dev1",
      description="Merger-tree for FoF, Rockstar, and consistent-trees based on yt.",
      author="Britton Smith",
      author_email="brittonsmith@gmail.com",
      license="BSD",
      keywords=["simulation", "merger-tree", "astronomy", "astrophysics"],
      url="https://github.com/brittonsmith/ytree",
      packages=["ytree"],
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
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
      ],
      install_requires=[
          'configparser',
          'h5py',
          'numpy',
          'yt>=3.4',
      ],
)

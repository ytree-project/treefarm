.. _developing:

Developer Guide
===============

treefarm is developed using the same conventions as yt.  The `yt
Developer Guide <https://yt-project.org/docs/dev/developing/index.html>`_
is a good reference for code style, communication with other developers,
working with git, and issuing pull requests.  Below is a brief guide of
aspects that are specific to treefarm.

Contributing in a Nutshell
--------------------------

Step zero, get out of that nutshell!

After that, the process for making contributions to treefarm is roughly as
follows:

1. Fork the `main treefarm repository <https://github.com/ytree-project/treefarm>`__.

2. Create a new branch.

3. Make changes.

4. Run tests.  Return to step 3, if needed.

5. Issue pull request.

The yt Developer Guide and `github <https://github.com/>`__ documentation
will help with the mechanics of git and pull requests.

Testing
-------

The treefarm source comes with a series of tests that can be run to
ensure nothing unexpected happens after changes have been made.  These
tests will automatically run when a pull request is issued or updated,
but they can also be run locally very easily.  At present, the suite
of tests for treefarm takes about three minutes to run.

Testing Data
^^^^^^^^^^^^

The first order of business is to obtain the sample datasets.  See
:ref:`sample-data` for how to do so.  Next, treefarm must be configure to
know the location of this data.  This is done by creating a configuration
file in your home directory at the location ``~/.config/treefarm/treefarmrc``.

.. code-block:: bash

   $ mkdir -p ~/.config/treefarm
   $ echo [treefarm] > ~/.config/treefarm/treefarmrc
   $ echo test_data_dir = /Users/britton/treefarm_data >> ~/.config/treefarm/treefarmrc
   $ cat ~/.config/treefarm/treefarmrc
   [treefarm]
   test_data_dir = /Users/britton/treefarm_data

This path should point to the outer directory containing all the
sample datasets.

Installing Development Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A number of additional packages are required for testing. These can be
installed with pip from within the ``treefarm`` source by doing:

.. code-block:: bash

   $ pip install -e .[dev]

To see how these dependencies are defined, have a look at the
``extras_require`` keyword argument in the ``setup.py`` file.

Run the Tests
^^^^^^^^^^^^^

The tests are run from the top level of the treefarm source.

.. code-block:: bash

   $ pytest tests
   ============================= test session starts ==============================
   platform darwin -- Python 3.7.1, pytest-4.1.1, py-1.7.0, pluggy-0.8.1
   rootdir: /Users/britton/Documents/work/yt/extensions/treefarm, inifile:
   plugins: cov-2.6.1
   collected 3 items

   tests/test_flake8.py .                                                   [ 33%]
   tests/test_treefarm.py ..                                                [100%]

   ========================== 3 passed in 61.73 seconds ===========================

Great job!

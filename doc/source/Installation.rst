.. _installation:

Installation
============

``treefarm``'s main dependencies are `yt <https://yt-project.org/>`_ and
`ytree <https://ytree.readthedocs.io>`_. If you manage packages with
something like `miniconda <https://docs.conda.io/en/latest/miniconda.html>`__,
then you can use ``pip`` to install ``treefarm`` after downloading the source.
In the future, ``treefarm`` will be installable directly from ``pip``. For now,
do the following:

.. code-block:: bash

   $ git clone https://github.com/ytree-project/treefarm
   $ cd treefarm
   $ pip install -e .

What version do I have?
=======================

To see what version of ``treefarm`` you are using, do the following:

.. code-block:: python

   import treefarm
   print (treefarm.__version__)

"""
Arbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from collections import \
    defaultdict
import functools
import h5py
import glob
import numpy as np
import os
import warnings

from yt.convenience import \
    load as yt_load
from yt.extern.six import \
    add_metaclass, \
    string_types
from yt.frontends.ytdata.utilities import \
    save_as_dataset, \
    _hdf5_yt_array
from yt.funcs import \
    get_pbar, \
    get_output_filename
from yt.units.dimensions import \
    length
from yt.units.unit_registry import \
    UnitRegistry
from yt.units.yt_array import \
    UnitParseError, \
    YTArray, \
    YTQuantity
from yt.utilities.cosmology import \
    Cosmology

from ytree.tree_node import \
    TreeNode
from ytree.tree_node_selector import \
    tree_node_selector_registry
from ytree.utilities.io import \
    _hdf5_yt_attr
from ytree.utilities.logger import \
    ytreeLogger as mylog

arbor_registry = {}

class RegisteredArbor(type):
    """
    Add to the registry of known Arbor classes to cycle
    through in the load function.
    """
    def __init__(cls, name, b, d):
        type.__init__(cls, name, b, d)
        arbor_type = name[:name.rfind("Arbor")]
        if arbor_type:
            arbor_registry[arbor_type] = cls

@add_metaclass(RegisteredArbor)
class Arbor(object):
    """
    Base class for all Arbor classes.

    Loads a merger-tree output file or a series of halo catalogs
    and create trees, stored in a list in :func:`~ytree.arbor.Arbor._trees`.
    Arbors can be saved in a universal format with
    :func:`~ytree.arbor.Arbor.save_arbor`.  Also, provide some convenience
    functions for creating YTArrays and YTQuantities and a cosmology
    calculator.
    """
    def __init__(self, filename):
        """
        Initialize an Arbor given a single input file.
        """
        self.filename = filename
        self.basename = os.path.basename(filename)
        self.unit_registry = UnitRegistry()
        self._load_trees()
        # self.field_list = self._field_data.keys()
        # self._set_default_selector()
        # self._root_field_data = {}
        self._set_comoving_units()
        self.cosmology = Cosmology(
            hubble_constant=self.hubble_constant,
            omega_matter=self.omega_matter,
            omega_lambda=self.omega_lambda,
            unit_registry=self.unit_registry)

    def __repr__(self):
        return self.basename

    def __getitem__(self, key):
        """
        If given a string, return an array of field values for the
        roots of all trees.
        If given an integer, return a tree from the list of trees.

        """
        if isinstance(key, string_types):
            if key in ("tree", "prog"):
                raise SyntaxError("Argument must be a field or integer.")
            if key not in self._root_field_data:
                self._root_field_data[key] = self.arr([t[key] for t in self])
            return self._root_field_data[key]
        return self._trees[key]

    def _get_field(self, field):
        """
        Get field data from cache or from disk.
        """
        return self._field_data[field]

    def __iter__(self):
        """
        Iterate over all items in the tree list.
        """
        for t in self._trees:
            yield t

    def __len__(self):
        """
        Return length of tree list.
        """
        return self._trees.size

    @property
    def size(self):
        """
        Return length of tree list.
        """
        return self._trees.size

    _unit_registry = None
    @property
    def unit_registry(self):
        return self._unit_registry

    @unit_registry.setter
    def unit_registry(self, value):
        self._unit_registry = value
        self._arr = None
        self._quan = None

    _box_size = None
    @property
    def box_size(self):
        return self._box_size

    @box_size.setter
    def box_size(self, value):
        self._box_size = value
        # set unitary as soon as we know the box size
        self.unit_registry.add(
            "unitary", float(self.box_size.in_base()), length)

    def _set_comoving_units(self):
        """
        Set "cm" units for explicitly comoving.
        Note, we are using comoving units all the time since
        we are dealing with data at multiple redshifts.
        """
        for my_unit in ["m", "pc", "AU", "au"]:
            new_unit = "%scm" % my_unit
            self._unit_registry.add(
                new_unit, self._unit_registry.lut[my_unit][0],
                length, self._unit_registry.lut[my_unit][3])

    def set_selector(self, selector, *args, **kwargs):
        r"""
        Sets the tree node selector to be used.

        This sets the manner in which halo ancestors are chosen
        from a list of ancestors when using the
        :func:`~ytee.tree_node.TreeNode._line` function to query fields
        for a tree.  The most obvious example is to always select
        the most massive ancestor so as to trace a halo's main
        progenitor.

        Parameters
        ----------
        selector : string
            Name of the selector to be used.

        Any additional arguments and keywords to be provided to
        the selector function should follow.

        Examples
        --------

        >>> import ytree
        >>> a = ytree.load("rockstar_halos/trees/tree_0_0_0.dat")
        >>> a.set_selector("max_field_value", "mvir")

        """
        self.selector = tree_node_selector_registry.find(
            selector, *args, **kwargs)

    _arr = None
    @property
    def arr(self):
        """
        Create a YTArray using the Arbor's unit registry.
        """
        if self._arr is not None:
            return self._arr
        self._arr = functools.partial(YTArray,
                                      registry=self.unit_registry)
        return self._arr

    _quan = None
    @property
    def quan(self):
        """
        Create a YTQuantity using the Arbor's unit registry.
        """
        if self._quan is not None:
            return self._quan
        self._quan = functools.partial(YTQuantity,
                                       registry=self.unit_registry)
        return self._quan

    def _set_default_selector(self):
        """
        Set the default tree node selector.

        Search for a mass-like field and use that with the
        max_field_value selector.
        """
        for field in ["particle_mass", "mvir"]:
            if field in self._field_data:
                self.set_selector("max_field_value", field)

    def _set_halo_id_field(self):
        """
        Figure out which field represents the halo IDs.
        """
        _hfields = ["halo_id", "particle_identifier"]
        hfields = [f for f in _hfields
                   if f in self._field_data]
        if len(hfields) == 0:
            raise RuntimeError("No halo id field found.")
        self._hid_field = hfields[0]

    def _load_trees(self):
        """
        Main function responsible for loading the trees.
        """
        pass

    @classmethod
    def _is_valid(cls, *args, **kwargs):
        """
        Check if input file works with a specific Arbor class.
        This is used with :func:`~ytree.arbor.load` function.
        """
        return False

    def save_arbor(self, filename=None, fields=None):
        r"""
        Save the arbor to a file.

        The saved arbor can be re-loaded as an arbor.

        Parameters
        ----------
        filename : optional, string
            Output filename.  Include a trailing "/" to indicate
            a directory.
            Default: "arbor.h5"
        fields : optional, list of strings
            The fields to be saved.  If not given, all
            fields will be saved.

        Returns
        -------
        filename : string
            The filename of the saved arbor.

        Examples
        --------

        >>> import ytree
        >>> a = ytree.load("rockstar_halos/trees/tree_0_0_0.dat")
        >>> fn = a.save_arbor()
        >>> # reload it
        >>> a2 = ytree.load(fn)

        """
        filename = get_output_filename(filename, "arbor", ".h5")
        if fields is None:
            fields = self.field_list
        ds = {}
        for attr in ["hubble_constant",
                     "omega_matter",
                     "omega_lambda"]:
            if hasattr(self, attr):
                ds[attr] = getattr(self, attr)
        extra_attrs = {"box_size": self.box_size,
                       "arbor_type": "ArborArbor",
                       "unit_registry_json": self.unit_registry.to_json()}
        save_as_dataset(ds, filename, self._field_data,
                        extra_attrs=extra_attrs)
        return filename

class MonolithArbor(Arbor):
    """
    Base class for Arbors loaded from a single file.
    """
    def _load_field_data(self):
        """
        Load all fields from file, store in self._field_data.
        """
        pass

    def _load_trees(self):
        """
        Create the tree structure.
        """
        self._load_field_data()
        self._set_halo_id_field()

        self._trees = []
        root_ids = self._field_data["uid"][self._field_data["desc_id"] == -1]
        if hasattr(root_ids, "units"):
            root_ids = root_ids.d
        root_ids = root_ids.astype(np.int64, copy=False)
        pbar = get_pbar("Loading %d trees" % root_ids.size,
                        self._field_data["uid"].size)
        for root_id in root_ids:
            tree_halos = (root_id == self._field_data["tree_id"])
            my_tree = {}
            for i in np.where(tree_halos)[0]:
                desc_id = np.int64(self._field_data["desc_id"][i])
                uid = np.int64(self._field_data["uid"][i])
                my_node = TreeNode(i, arbor=self)
                my_tree[uid] = my_node
                if desc_id >= 0:
                    my_tree[desc_id].add_ancestor(my_node)
                pbar.update(1)
            self._trees.append(my_tree[root_id])
        pbar.finish()
        self._trees = np.array(self._trees)
        mylog.info("Arbor contains %d trees with %d total nodes." %
                   (self._trees.size, self._field_data["uid"].size))

class ArborArbor(MonolithArbor):
    """
    Class for Arbors created from the :func:`~ytree.arbor.Arbor.save_arbor`
    or :func:`~ytree.tree_node.TreeNode.save_tree` functions.
    """
    def _load_field_data(self):
        """
        All data stored in a single hdf5 file.  Get cosmological
        parameters and modify unit registry for hubble constant.
        """
        fh = h5py.File(self.filename, "r")
        for attr in ["hubble_constant",
                     "omega_matter",
                     "omega_lambda"]:
            setattr(self, attr, fh.attrs[attr])
        if "unit_registry_json" in fh.attrs:
            self.unit_registry = \
              UnitRegistry.from_json(
                  fh.attrs["unit_registry_json"].astype(str))
        self.unit_registry.modify("h", self.hubble_constant)
        self.box_size = _hdf5_yt_attr(fh, "box_size",
                                      unit_registry=self.unit_registry)
        self._field_data = dict([(f, _hdf5_yt_array(fh["data"], f, self))
                                 for f in fh["data"]])
        fh.close()

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .h5, be loadable as an hdf5 file,
        and have "arbor_type" attribute.
        """
        fn = args[0]
        if not fn.endswith(".h5"): return False
        try:
            with h5py.File(fn, "r") as f:
                if "arbor_type" not in f.attrs:
                    return False
                if f.attrs["arbor_type"].astype(str) != "ArborArbor":
                    return False
        except:
            return False
        return True

class ConsistentTreesArbor(MonolithArbor):
    """
    Class for Arbors from consistent-trees output files.
    """
    def _set_default_selector(self):
        """
        Mass is "mvir".
        """
        self.set_selector("max_field_value", "mvir")

    def _parse_parameter_file(self):
        """
        Read all relevant parameters from file header and
        modify unit registry for hubble constant.
        """

        self._field_data = {}
        fields = []
        fi = {}
        fdb = {}
        rems = ["%s%s%s" % (s[0], t, s[1])
                for s in [("(", ")"), ("", "")]
                for t in ["comoving", "physical"]]

        f = open(self.filename, "r")
        self._file_size = f.seek(0, 2)
        f.seek(0)

        # Read the first line as a list of all fields.
        # Do some footwork to remove awkard characters.
        rfl = f.readline()[1:].strip().split()
        for pf in rfl:
            if "(" in pf and ")" in pf:
                bt = pf[pf.find("(")+1:pf.rfind(")")]
                if bt.isdigit():
                    fields.append(pf[:pf.find("(")])
                else:
                    fields.append(pf)
            else:
                fields.append(pf)

        # Now grab a bunch of things from the header.
        while True:
            line = f.readline()
            if line is None:
                raise IOError(
                    "Encountered enexpected EOF reading %s." %
                    self.filename)
            elif not line.startswith("#"):
                n_halos = int(line.strip())
                break
            # cosmological parameters
            if "Omega_M" in line:
                pars = line[1:].split(";")
                for j, par in enumerate(["omega_matter",
                                         "omega_lambda",
                                         "hubble_constant"]):
                    v = float(pars[j].split(" = ")[1])
                    setattr(self, par, v)
            # box size
            elif "Full box size" in line:
                pars = line.split("=")[1].strip().split()
                box = pars

            # These are lines describing the various fields.
            # Pull them apart and look for units.
            elif ":" in line:
                tfields, desc = line[1:].strip().split(":", maxsplit=1)
                for sep in ["/", ","]:
                    if sep in tfields:
                        tfields = tfields.split(sep)
                if not isinstance(tfields, list):
                    tfields = [tfields]
                for tfield in tfields:
                    punits = ""
                    if "(" in line and ")" in line:
                        punits = desc[desc.find("(")+1:desc.rfind(")")]
                        for rem in rems:
                            while rem in punits:
                                pre, mid, pos = punits.partition(rem)
                                punits = pre + pos
                        try:
                            x = self.quan(1, punits)
                        except UnitParseError:
                            pass
                    fdb[tfield.lower()] = \
                      {"description": desc.strip(),
                       "units": punits}
        self._hoffset = f.tell()

        # Create root nodes and calculate file offsets.
        self._trees = np.empty(n_halos, dtype=np.object)
        treech = f.read().split("#")
        offset = self._hoffset + 1 # for the first #
        last_off = 0
        for i, treel in enumerate(treech[1:]):
            loff = treel.find("\n")
            uid = int(treel[5:loff])
            offset += len(treech[i]) + loff - last_off + 1
            last_off = loff
            my_node = TreeNode(uid, arbor=self)
            my_node.offset = offset
            self._trees[i] = my_node
        f.close()

        # Fill the field info with the units found above.
        for i, field in enumerate(fields):
            if "(" in field and ")" in field:
                cfield = field[:field.find("(")]
            else:
                cfield = field
            fi[field] = fdb.get(field.lower(),
                                {"description": "",
                                 "units": ""})
            fi[field]["column"] = i
        self.field_list = fields
        self.field_info = fi

        self.unit_registry.modify("h", self.hubble_constant)
        self.box_size = self.quan(float(box[0]), box[1])

    def _load_trees(self):
        """
        For now, just parse the parameter file.
        """
        mylog.info("Loading tree data from %s." % self.filename)
        self._parse_parameter_file()

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .dat and have a line in the header
        with the string, "Consistent Trees".
        """
        fn = args[0]
        if not fn.endswith(".dat"): return False
        with open(fn, "r") as f:
            valid = False
            while True:
                line = f.readline()
                if line is None or not line.startswith("#"):
                    break
                if "Consistent Trees" in line:
                    valid = True
                    break
            if not valid: return False
        return True

class CatalogArbor(Arbor):
    """
    Base class for Arbors created from a series of halo catalog
    files where the descendent ID for each halo has been
    pre-determined.
    """
    def _get_all_files(self):
        """
        Get all input files based on specific naming convention.
        """
        pass

    def _load_field_data(self, *args):
        """
        Load field data from a single halo catalog.
        """
        pass

    def _to_field_array(self, field, data):
        """
        Determines how final field arrays are defined, assigns
        units if they have been pre-defined.
        """
        if len(data) == 0:
            return np.array(data)
        if isinstance(data[0], YTArray):
            # Override the dataset's units with the arbor's
            # to avoid lingering comoving/proper definitions.
            self._field_data[field] = \
              self.arr(data, str(data[0].units))
        else:
            self._field_data[field] = np.array(data)

    def _load_trees(self):
        """
        Create the tree structure from the input files.
        """
        my_files = self._get_all_files()
        self._field_data = defaultdict(list)

        offset = 0
        anc_ids = None
        anc_nodes = None
        my_trees = []
        pbar = get_pbar("Load halo catalogs", len(my_files))
        for i, fn in enumerate(my_files):
            n_halos = self._load_field_data(fn, offset)
            if n_halos == 0:
                pbar.update(i)
                continue

            my_nodes = []
            for halo in range(n_halos):
                my_node = TreeNode(self._field_data["uid"][-1][halo],
                                   arbor=self)
                my_nodes.append(my_node)
                if self._field_data["desc_id"][-1][halo] == -1 or i == 0:
                    my_trees.append(my_node)

            if anc_ids is not None:
                des_ids = anc_ids
                des_nodes = anc_nodes
            anc_ids = self._field_data["halo_id"][-1]
            anc_nodes = my_nodes

            offset += n_halos
            if i == 0:
                pbar.update(i)
                continue

            for halo in range(n_halos):
                des_id = self._field_data["desc_id"][-1][halo]
                if des_id == -1: continue
                i_des = np.where(des_id == des_ids)[0][0]
                des_nodes[i_des].add_ancestor(anc_nodes[halo])

            pbar.update(i)
        pbar.finish()
        self._trees = np.array(my_trees)

        for field in self._field_data:
            my_data = []
            for level in self._field_data[field]:
                my_data.extend(level)
            self._to_field_array(field, my_data)

        self._field_data["tree_id"] = -np.ones(offset)
        for t in self._trees:
            self._field_data["tree_id"][t._tree_field_indices] = t["uid"]
            for tnode in t.twalk():
                if tnode.ancestors is None: continue
                for a in tnode.ancestors:
                    self._field_data["desc_id"][a.uid] = tnode["uid"]
        assert (self._field_data["tree_id"] != -1).any()

        mylog.info("Arbor contains %d trees with %d total nodes." %
                   (self._trees.size, offset))

_rs_columns = (("halo_id",  (0,)),
               ("desc_id",  (1,)),
               ("mvir",     (2,)),
               ("rvir",     (5,)),
               ("position", (8, 9, 10)),
               ("velocity", (11, 12, 13)))
_rs_units = {"mvir": "Msun/h",
             "rvir": "kpc/h",
             "position": "Mpc/h",
             "velocity": "km/s"}
_rs_type = {"halo_id": np.int64,
            "desc_id": np.int64}
_rs_usecol = []
_rs_fields = {}
for field, col in _rs_columns:
    _rs_usecol.extend(col)
    _rs_fields[field] = np.arange(len(_rs_usecol)-len(col),
                                  len(_rs_usecol))

class RockstarArbor(CatalogArbor):
    """
    Class for Arbors created from Rockstar out_*.list files.
    Use only descendent IDs to determine tree relationship.
    """
    def _get_all_files(self):
        """
        Get all out_*.list files and put them in reverse order.
        """
        prefix = self.filename.rsplit("_", 1)[0]
        suffix = ".list"
        my_files = glob.glob("%s_*%s" % (prefix, suffix))
        # sort by catalog number
        my_files.sort(key=lambda x:
                      int(x[x.find(prefix)+len(prefix)+1:x.rfind(suffix)]),
                      reverse=True)
        return my_files

    def _to_field_array(self, field, data):
        """
        Use field definitions from above to assign units
        for field arrays.
        """
        if field in _rs_units:
            self._field_data[field] = self.arr(data, _rs_units[field])
        else:
            self._field_data[field] = np.array(data)

    def _read_parameters(self, filename):
        """
        Read header file to get cosmological parameters
        and modify unit registry for hubble constant.
        """
        get_pars = not hasattr(self, "hubble_constant")
        f = open(filename, "r")
        while True:
            line = f.readline()
            if line is None or not line.startswith("#"):
                break
            if get_pars and line.startswith("#Om = "):
                pars = line[1:].split(";")
                for j, par in enumerate(["omega_matter",
                                         "omega_lambda",
                                         "hubble_constant"]):
                    v = float(pars[j].split(" = ")[1])
                    setattr(self, par, v)
            if get_pars and line.startswith("#Box size:"):
                pars = line.split(":")[1].strip().split()
                box = pars
            if line.startswith("#a = "):
                a = float(line.split("=")[1].strip())
        f.close()
        if get_pars:
            self.unit_registry.modify("h", self.hubble_constant)
            self.box_size = self.quan(float(box[0]), box[1])
        return 1. / a - 1.

    def _load_field_data(self, fn, offset):
        """
        Load field data using np.loadtxt.
        Create a redshift field and uid field.
        """
        with warnings.catch_warnings():
            # silence empty file warnings
            warnings.simplefilter("ignore", category=UserWarning,
                                  append=1, lineno=893)
            data = np.loadtxt(fn, unpack=True, usecols=_rs_usecol)
        z = self._read_parameters(fn)
        if data.size == 0:
            return 0

        if len(data.shape) == 1:
            data = np.reshape(data, (data.size, 1))
        n_halos = data.shape[1]
        self._field_data["redshift"].append(z * np.ones(n_halos))
        self._field_data["uid"].append(np.arange(offset, offset+n_halos))
        for field, cols in _rs_fields.items():
            if cols.size == 1:
                self._field_data[field].append(data[cols][0])
            else:
                self._field_data[field].append(np.rollaxis(data[cols], 1))
            if field in _rs_type:
                self._field_data[field][-1] = \
                  self._field_data[field][-1].astype(_rs_type[field])
        return n_halos

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .list.
        """
        fn = args[0]
        if not fn.endswith(".list"): return False
        return True

class TreeFarmArbor(CatalogArbor):
    """
    Class for Arbors created with :class:`~ytree.tree_farm.TreeFarm`.
    """
    def _set_default_selector(self):
        """
        Mass is "particle_mass".
        """
        self.set_selector("max_field_value", "particle_mass")

    def _get_all_files(self):
        """
        Get all files and put in reverse order.
        """
        prefix = self.filename.rsplit("_", 1)[0]
        suffix = ".h5"
        my_files = glob.glob("%s_*%s" % (prefix, suffix))
        # sort by catalog number
        my_files.sort(key=lambda x:
                      int(x[x.find(prefix)+len(prefix)+1:x.find(".0")]),
                      reverse=True)
        return my_files

    def _load_field_data(self, fn, offset):
        """
        Load field data as a yt HaloCatalog dataset.
        Get cosmological parameters and modify unit registry
        for hubble constant.
        Create a redshift field and uid field and rename
        particle_identifier and descendent_identifier to halo_id
        and desc_id.
        """
        ds = yt_load(fn)

        if not hasattr(self, "hubble_constant"):
            for attr in ["hubble_constant",
                         "omega_matter",
                         "omega_lambda"]:
                setattr(self, attr, getattr(ds, attr))
            self.unit_registry.modify("h", self.hubble_constant)
            # Drop the "cm" suffix because all lengths will
            # be in comoving units.
            self.box_size = self.quan(
                ds.domain_width[0].to("Mpccm/h"), "Mpc/h")
        try:
            if len(ds.field_list) == 0 or ds.index.total_particles == 0:
                return 0
        except ValueError:
            return 0
        skip_fields = ["particle_identifier", "descendent_identifier"]
        add_fields = [("halos", field)
                      for field in ["particle_position",
                                    "particle_velocity"]]
        for field in ds.field_list + add_fields:
            if field[0] != "halos": continue
            if "particle_position_" in field[1]: continue
            if "particle_velocity_" in field[1]: continue
            if field[1] in skip_fields: continue
            field_data = ds.r[field]
            if field_data.units.dimensions is length:
                field_data.convert_to_units("unitary")
            self._field_data[field[1]].append(field_data)
        self._field_data["halo_id"].append(
          ds.r["halos", "particle_identifier"].d.astype(np.int64))
        self._field_data["desc_id"].append(
          ds.r["halos", "descendent_identifier"].d.astype(np.int64))
        n_halos = self._field_data["halo_id"][-1].size
        self._field_data["redshift"].append(
            ds.current_redshift * np.ones(n_halos))
        self._field_data["uid"].append(
            np.arange(offset, offset+n_halos))
        return n_halos

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .h5, be loadable as an hdf5 file,
        and have a "data_type" attribute.
        """
        fn = args[0]
        if not fn.endswith(".h5"): return False
        try:
            with h5py.File(fn, "r") as f:
                if "data_type" not in f.attrs:
                    return False
                if f.attrs["data_type"].astype(str) != "halo_catalog":
                    return False
        except:
            return False
        return True

def load(filename, method=None):
    """
    Load an Arbor, determine the type automatically.

    Parameters
    ----------
    filename : string
        Input filename.
    method : optional, string
        The type of Arbor to be loaded.  Existing types are:
        Arbor, ConsistentTrees, Rockstar, TreeFar.  If not
        given, the type will be determined based on characteristics
        of the input file.

    Returns
    -------
    Arbor

    Examples
    --------

    >>> import ytree
    >>> # saved Arbor
    >>> a = ytree.load("arbor.h5")
    >>> # consistent-trees output
    >>> a = ytree.load("rockstar_halos/trees/tree_0_0_0.dat")
    >>> # Rockstar catalogs
    >>> a = ytree.load("rockstar_halos/out_0.list")
    >>> # TreeFarm catalogs
    >>> a = ytree.load("my_halos/fof_subhalo_tab_025.0.hdf5.0.h5")

    """
    if not os.path.exists(filename):
        raise IOError("file does not exist: %s." % filename)
    if method is None:
        candidates = []
        for candidate, c in arbor_registry.items():
            if c._is_valid(filename):
                candidates.append(candidate)
        if len(candidates) == 0:
            raise IOError("Could not determine arbor type for %s." % filename)
        elif len(candidates) > 1:
            errmsg = "Could not distinguish between these arbor types:\n"
            for candidate in candidates:
                errmsg += "Possible: %s.\n" % candidate
            errmsg += "Provide one of these types using the \'method\' keyword."
            raise IOError(errmsg)
        else:
            method = candidates[0]
    else:
        if method not in arbor_registry:
            raise IOError("Invalid method: %s.  Available: %s." %
                          (method, arbor_registry.keys()))
    return arbor_registry[method](filename)

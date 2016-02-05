import h5py
import glob
import numpy as np
import os
import yt

class TreeNode(object):
    def __init__(self, halo_id, level_id, global_id=None):
        self.halo_id = halo_id
        self.level_id = level_id
        self.global_id = global_id
        self.ancestors = None

    def add_ancestor(self, ancestor):
        if self.ancestors is None:
            self.ancestors = []
        self.ancestors.append(ancestor)

    def __repr__(self):
        return "TreeNode[%d,%d]" % (self.level_id, self.halo_id)

def get_ancestry_arrays(knot, fields):
    data = dict([(field, []) for field in fields])
    my_knot = knot
    while my_knot is not None:
        for field in fields:
            data[field].append(getattr(my_knot, field))
        if my_knot.ancestors is not None and \
          len(my_knot.ancestors) > 0:
            my_knot = my_knot.ancestors[0]
        else:
            my_knot = None
    for field in data:
        data[field] = yt.YTArray(data[field])
    return data

class Arbor(object):
    def __init__(self, output_dir, fields=None):
        self.output_dir = output_dir
        if fields is None:
            fields = []
        self.fields = fields
        self._load_tree()

    def _load_tree(self):
        my_files = glob.glob(os.path.join(self.output_dir, "tree_segment_*.h5"))
        my_files.sort()

        self._field_data = dict([(f, []) for f in self.fields])

        offset = 0
        my_tree = None
        for i, fn in enumerate(my_files):
            fh = h5py.File(fn, "r")
            if my_tree is None:
                des_ids = fh["data/descendent_particle_identifier"].value
                for field in self.fields:
                    self._field_data[field].append(fh["data/descendent_%s" % field].value)
            else:
                des_ids = anc_ids
            anc_ids = fh["data/ancestor_particle_identifier"].value
            for field in self.fields:
                self._field_data[field].append(fh["data/ancestor_%s" % field].value)
            links = fh["data/links"].value
            fh.close()

            if my_tree is None:
                des_nodes = [TreeNode(my_id, i, gid+offset)
                             for gid, my_id in enumerate(des_ids)]
                my_tree = des_nodes
                offset += des_ids.size
            else:
                des_nodes = anc_nodes

            anc_nodes = [TreeNode(my_id, i+1, gid+offset)
                         for gid, my_id in enumerate(anc_ids)]
            offset += anc_ids.size

            for link in links:
                i_des = np.where(link[0] == des_ids)[0][0]
                i_anc = np.where(link[1] == anc_ids)[0][0]
                des_nodes[i_des].add_ancestor(anc_nodes[i_anc])

        self.tree = my_tree

        for field in self._field_data:
            my_data = []
            for level in self._field_data[field]:
                my_data.extend(level)
            self._field_data[field] = np.array(my_data)

        yt.mylog.info("Arbor contains %d trees with %d total halos." %
                      (len(self.tree), offset))

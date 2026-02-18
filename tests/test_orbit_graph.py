# Copyright (c) 2022, MASSACHUSETTS INSTITUTE OF TECHNOLOGY
# Subject to FAR 52.227-11 – Patent Rights – Ownership by the Contractor (May 2014).
# SPDX-License-Identifier: MIT

import pytest
from orbit_defender2d.utils.orbit_grid import OrbitGrid
from orbit_defender2d.utils.orbit_graph import OrbitGraph
import orbit_defender2d.utils.utils as U


board_cases = [
    (2),
    (3),
    (4)]

@pytest.mark.parametrize(
    "num_rings",board_cases)
def test_orbit_graph_nodes(num_rings):
    ogrid = OrbitGrid(num_rings)
    ograph = OrbitGraph(ogrid)
    assert ogrid.n_sectors == len(list(ograph.adj_graph))
    assert ogrid.n_sectors == len(list(ograph.move_graph))
    assert ogrid.n_sectors == len(list(ograph.turn_graph))


# ---- Adjacency graph tests ----

@pytest.mark.parametrize("num_rings", board_cases)
def test_adj_graph_is_symmetric(num_rings):
    '''adjacency graph should be undirected (symmetric edges)'''
    ogrid = OrbitGrid(num_rings)
    ograph = OrbitGraph(ogrid)
    for u, v in ograph.adj_graph.edges():
        assert ograph.adj_graph.has_edge(v, u), \
            f"adj_graph edge ({u},{v}) exists but ({v},{u}) does not"

@pytest.mark.parametrize("num_rings", board_cases)
def test_adj_graph_has_self_loops(num_rings):
    '''the adjacency graph includes self-loops for all sectors
    due to the distance-0 azimuth check'''
    ogrid = OrbitGrid(num_rings)
    ograph = OrbitGraph(ogrid)
    for node in ograph.adj_graph.nodes():
        assert ograph.adj_graph.has_edge(node, node)

@pytest.mark.parametrize("num_rings", board_cases)
def test_adj_graph_same_ring_neighbors(num_rings):
    '''sectors in ring 2+ should be adjacent to their azimuth neighbors'''
    ogrid = OrbitGrid(num_rings)
    ograph = OrbitGraph(ogrid)
    for sec in range(ogrid.n_sectors):
        ring = ogrid.sector_num2ring(sec)
        if ring < 2:
            continue
        pro = ogrid.get_prograde_sector(sec)
        ret = ogrid.get_retrograde_sector(sec)
        assert ograph.adj_graph.has_edge(sec, pro)
        assert ograph.adj_graph.has_edge(sec, ret)


# ---- adjacent() method tests ----

def test_adjacent_same_ring_neighbors():
    '''prograde and retrograde neighbors should be adjacent'''
    ogrid = OrbitGrid(3)
    ograph = OrbitGraph(ogrid)
    # ring 2 has sectors 3,4,5,6 (azim 0,1,2,3)
    assert ograph.adjacent(3, 4)  # azim 0 and 1
    assert ograph.adjacent(4, 3)  # symmetric
    assert ograph.adjacent(5, 6)  # azim 2 and 3

def test_adjacent_same_ring_wraparound():
    '''first and last sector in a ring should be adjacent (wraparound)'''
    ogrid = OrbitGrid(3)
    ograph = OrbitGraph(ogrid)
    # ring 3 has sectors 7..14 (azim 0..7)
    assert ograph.adjacent(7, 14)  # azim 0 and azim 7 (wraparound)
    assert ograph.adjacent(14, 7)

def test_adjacent_radial_neighbors():
    '''sectors in adjacent rings that share a boundary should be adjacent'''
    ogrid = OrbitGrid(3)
    ograph = OrbitGraph(ogrid)
    # sector 1 (ring 1, azim 0) should be adjacent to sectors 3,4 (ring 2, azim 0,1)
    assert ograph.adjacent(1, 3)
    assert ograph.adjacent(1, 4)

def test_not_adjacent_distant_sectors():
    '''sectors far apart should not be adjacent'''
    ogrid = OrbitGrid(3)
    ograph = OrbitGraph(ogrid)
    # sector 7 (ring 3, azim 0) and sector 11 (ring 3, azim 4) are not neighbors
    assert not ograph.adjacent(7, 11)

def test_adjacent_self():
    '''a sector is adjacent to itself (self-loops exist in adj_graph)'''
    ogrid = OrbitGrid(3)
    ograph = OrbitGraph(ogrid)
    assert ograph.adjacent(0, 0)
    assert ograph.adjacent(7, 7)


# ---- Movement graph tests ----

@pytest.mark.parametrize("num_rings", board_cases)
def test_move_graph_has_self_loops(num_rings):
    '''every sector should have a self-loop in move_graph'''
    ogrid = OrbitGrid(num_rings)
    ograph = OrbitGraph(ogrid)
    for node in ograph.move_graph.nodes():
        assert ograph.move_graph.has_edge(node, node), \
            f"sector {node} has no self-loop in move_graph"

@pytest.mark.parametrize("num_rings", board_cases)
def test_move_graph_noop_self_loops_ring2_plus(num_rings):
    '''sectors in ring 2+ have noop self-loops with weight 0'''
    ogrid = OrbitGrid(num_rings)
    ograph = OrbitGraph(ogrid)
    for node in ograph.move_graph.nodes():
        ring = ogrid.sector_num2ring(node)
        if ring < 2:
            continue  # ring 0/1 have special cases due to elif ordering
        assert ograph.move_graph[node][node]['weight'] == 0.0

@pytest.mark.parametrize("num_rings", board_cases)
def test_move_graph_prograde_edges_ring2_plus(num_rings):
    '''prograde movement in ring 2+ should create edges with correct fuel cost'''
    ogrid = OrbitGrid(num_rings)
    ograph = OrbitGraph(ogrid)
    for sec in range(ogrid.n_sectors):
        ring = ogrid.sector_num2ring(sec)
        if ring < 2:
            continue  # ring 0/1 prograde == retrograde, elif takes retrograde
        pro_sec = ogrid.get_prograde_sector(sec)
        assert ograph.move_graph.has_edge(sec, pro_sec), \
            f"no prograde edge from {sec} to {pro_sec}"
        assert ograph.move_graph[sec][pro_sec]['weight'] == 5.0  # default PROGRADE cost

@pytest.mark.parametrize("num_rings", board_cases)
def test_move_graph_retrograde_edges(num_rings):
    '''retrograde movement should create edges with correct fuel cost'''
    ogrid = OrbitGrid(num_rings)
    ograph = OrbitGraph(ogrid)
    for sec in range(ogrid.n_sectors):
        ring = ogrid.sector_num2ring(sec)
        if ring < 2:
            continue  # ring 0/1 have special overlap
        ret_sec = ogrid.get_retrograde_sector(sec)
        assert ograph.move_graph.has_edge(sec, ret_sec), \
            f"no retrograde edge from {sec} to {ret_sec}"
        assert ograph.move_graph[sec][ret_sec]['weight'] == 10.0  # default RETROGRADE cost

@pytest.mark.parametrize("num_rings", board_cases)
def test_move_graph_radial_out_edges(num_rings):
    '''radial out movement should create edges except from outermost ring'''
    ogrid = OrbitGrid(num_rings)
    ograph = OrbitGraph(ogrid)
    for sec in range(ogrid.n_sectors):
        out_sec = ogrid.get_radial_out_sector(sec)
        if out_sec is not None:
            assert ograph.move_graph.has_edge(sec, out_sec), \
                f"no radial_out edge from {sec} to {out_sec}"
            assert ograph.move_graph[sec][out_sec]['weight'] == 1.0  # default RADIAL_OUT cost

@pytest.mark.parametrize("num_rings", board_cases)
def test_move_graph_radial_in_edges(num_rings):
    '''radial in movement should create edges except from innermost ring'''
    ogrid = OrbitGrid(num_rings)
    ograph = OrbitGraph(ogrid)
    for sec in range(ogrid.n_sectors):
        in_sec = ogrid.get_radial_in_sector(sec)
        if in_sec is not None:
            assert ograph.move_graph.has_edge(sec, in_sec), \
                f"no radial_in edge from {sec} to {in_sec}"
            assert ograph.move_graph[sec][in_sec]['weight'] == 1.0  # default RADIAL_IN cost


# ---- Turn graph tests ----

@pytest.mark.parametrize("num_rings", board_cases)
def test_turn_graph_has_edges(num_rings):
    '''turn graph should have edges representing combined movement + drift'''
    ogrid = OrbitGrid(num_rings)
    ograph = OrbitGraph(ogrid)
    assert ograph.turn_graph.number_of_edges() > 0

@pytest.mark.parametrize("num_rings", board_cases)
def test_turn_graph_self_loops_ring2_plus(num_rings):
    '''staying in the same sector in ring 2+ requires retrograde + drift'''
    ogrid = OrbitGrid(num_rings)
    ograph = OrbitGraph(ogrid)
    for sec in range(ogrid.n_sectors):
        ring = ogrid.sector_num2ring(sec)
        if ring < 2:
            continue  # ring 0 and ring 1 have special cases
        assert ograph.turn_graph.has_edge(sec, sec), \
            f"sector {sec} has no self-loop in turn_graph"
        assert ograph.turn_graph[sec][sec]['weight'] == 10.0 + 1.0  # RETROGRADE + DRIFT

def test_turn_graph_self_loop_ring1():
    '''ring 1 self-loops have prograde+drift weight due to elif ordering'''
    ogrid = OrbitGrid(3)
    ograph = OrbitGraph(ogrid)
    # ring 1 sectors: 1, 2
    assert ograph.turn_graph[1][1]['weight'] == 5.0 + 1.0  # PROGRADE + DRIFT
    assert ograph.turn_graph[2][2]['weight'] == 5.0 + 1.0

def test_turn_graph_self_loop_ring0():
    '''ring 0 self-loop has noop+drift weight'''
    ogrid = OrbitGrid(3)
    ograph = OrbitGraph(ogrid)
    assert ograph.turn_graph[0][0]['weight'] == 0.0 + 1.0  # NOOP + DRIFT


# ---- Custom FuelUsage tests ----

def test_custom_fuel_usage():
    '''OrbitGraph should respect custom fuel usage values'''
    ogrid = OrbitGrid(3)  # use 3 rings so we have ring 2 for clean prograde/retrograde
    custom_fuel = {
        U.NOOP: 0.0,
        U.DRIFT: 2.0,
        U.PROGRADE: 7.0,
        U.RETROGRADE: 15.0,
        U.RADIAL_IN: 3.0,
        U.RADIAL_OUT: 3.0,
        U.IN_SEC: {U.SHOOT: 5.0, U.COLLIDE: 20.0, U.GUARD: 20.0},
        U.ADJ_SEC: {U.SHOOT: 5.0, U.COLLIDE: 30.0, U.GUARD: 30.0},
    }
    ograph = OrbitGraph(ogrid, FuelUsage=custom_fuel)

    # ring 2 sectors (3..6) have unambiguous prograde/retrograde
    sec = 3  # ring 2, azim 0
    pro_sec = ogrid.get_prograde_sector(sec)  # sector 4
    assert ograph.move_graph[sec][pro_sec]['weight'] == 7.0

    ret_sec = ogrid.get_retrograde_sector(sec)  # sector 6
    assert ograph.move_graph[sec][ret_sec]['weight'] == 15.0

    # noop self-loop for ring 2
    assert ograph.move_graph[sec][sec]['weight'] == 0.0

    # radial edges
    out_sec = ogrid.get_radial_out_sector(sec)
    if out_sec is not None:
        assert ograph.move_graph[sec][out_sec]['weight'] == 3.0

def test_fuel_usage_drift_auto_added():
    '''if DRIFT not in FuelUsage, it should be auto-added with default 1.0'''
    ogrid = OrbitGrid(2)
    custom_fuel = {
        U.NOOP: 0.0,
        U.PROGRADE: 5.0,
        U.RETROGRADE: 10.0,
        U.RADIAL_IN: 1.0,
        U.RADIAL_OUT: 1.0,
        U.IN_SEC: {U.SHOOT: 5.0, U.COLLIDE: 20.0, U.GUARD: 20.0},
        U.ADJ_SEC: {U.SHOOT: 5.0, U.COLLIDE: 30.0, U.GUARD: 30.0},
    }
    # should not raise - drift auto-added
    ograph = OrbitGraph(ogrid, FuelUsage=custom_fuel)
    assert ograph.turn_graph.number_of_edges() > 0

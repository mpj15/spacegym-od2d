# Copyright (c) 2022, MASSACHUSETTS INSTITUTE OF TECHNOLOGY
# Subject to FAR 52.227-11 – Patent Rights – Ownership by the Contractor (May 2014).
# SPDX-License-Identifier: MIT

import pytest
from orbit_defender2d.utils import utils as U

from hypothesis import given, strategies as st

# ---- int2bitlist / bitlist2int round-trip tests ----

@given(st.integers(min_value=0))
def test_hypothesis_int2bitlist(n):
    '''test int to binary conversion'''
    n_bit = U.int2bitlist(n)
    # reconstruct integer from binary
    n_int = 0
    for i, v in enumerate(reversed(n_bit)):
        n_int += v * 2**i
    assert n_int == n

@given(st.integers(min_value=0))
def test_hypothesis_int2bitlist_bitlist2in(n):
    '''test int to binary and binary to int conversion'''
    assert U.bitlist2int(U.int2bitlist(n)) == n

# ---- int2bitlist edge cases ----

def test_int2bitlist_zero():
    '''zero should produce [0]'''
    assert U.int2bitlist(0) == [0]

def test_int2bitlist_one():
    assert U.int2bitlist(1) == [1]

def test_int2bitlist_powers_of_two():
    '''powers of two should produce a 1 followed by zeros'''
    for exp in range(1, 10):
        result = U.int2bitlist(2**exp)
        assert result[0] == 1
        assert all(b == 0 for b in result[1:])
        assert len(result) == exp + 1

def test_int2bitlist_negative_raises():
    '''negative integers should raise AssertionError'''
    with pytest.raises(AssertionError):
        U.int2bitlist(-1)

# ---- bitlist2int edge cases ----

def test_bitlist2int_single_zero():
    assert U.bitlist2int([0]) == 0

def test_bitlist2int_single_one():
    assert U.bitlist2int([1]) == 1

def test_bitlist2int_known_values():
    assert U.bitlist2int([1, 0, 1]) == 5
    assert U.bitlist2int([1, 1, 0, 1]) == 13
    assert U.bitlist2int([1, 0, 0, 0, 0]) == 16

def test_bitlist2int_leading_zeros():
    '''leading zeros should not affect value'''
    assert U.bitlist2int([0, 0, 1, 0, 1]) == 5

# ---- Constants validation ----

def test_player_names():
    assert U.P1 == 'Alpha'
    assert U.P2 == 'Bravo'

def test_token_delimiter():
    assert U.TOKEN_DELIMITER == ':'

def test_turn_phase_list():
    assert U.TURN_PHASE_LIST == ['movement', 'engagement', 'drift']
    assert U.MOVEMENT == 'movement'
    assert U.ENGAGEMENT == 'engagement'
    assert U.DRIFT == 'drift'

def test_piece_roles():
    assert U.PIECE_ROLES == ['HVA', 'Patrol']
    assert U.SEEKER == 'HVA'
    assert U.BLUDGER == 'Patrol'

def test_movement_types():
    assert len(U.MOVEMENT_TYPES) == 5
    assert U.NOOP == 'noop'
    assert U.PROGRADE == 'prograde'
    assert U.RETROGRADE == 'retrograde'
    assert U.RADIAL_IN == 'radial_in'
    assert U.RADIAL_OUT == 'radial_out'

def test_engagement_types():
    assert len(U.ENGAGEMENT_TYPES) == 3
    assert U.SHOOT == 'shoot'
    assert U.COLLIDE == 'collide'
    assert U.GUARD == 'guard'

def test_sector_types():
    assert U.IN_SEC == 'in_sector'
    assert U.ADJ_SEC == 'adjacent_sector'

# ---- Namedtuple tests ----

def test_movement_tuple():
    mt = U.MovementTuple(action_type=U.PROGRADE)
    assert mt.action_type == U.PROGRADE
    # equality
    assert mt == U.MovementTuple(U.PROGRADE)
    assert mt != U.MovementTuple(U.NOOP)

def test_engagement_tuple():
    et = U.EngagementTuple(action_type=U.SHOOT, target='Bravo:HVA:0', prob=0.8)
    assert et.action_type == U.SHOOT
    assert et.target == 'Bravo:HVA:0'
    assert et.prob == 0.8

def test_engagement_tuple_equality_ignores_prob_when_none():
    '''EngagementTuples with None prob are used for legal action comparison'''
    et1 = U.EngagementTuple(U.SHOOT, 'Bravo:HVA:0', None)
    et2 = U.EngagementTuple(U.SHOOT, 'Bravo:HVA:0', None)
    assert et1 == et2

def test_engagement_outcome_tuple():
    eot = U.EngagementOutcomeTuple(
        action_type=U.SHOOT,
        attacker='Alpha:Patrol:1',
        target='Bravo:HVA:0',
        guardian=None,
        prob=0.8,
        success=True)
    assert eot.action_type == U.SHOOT
    assert eot.attacker == 'Alpha:Patrol:1'
    assert eot.target == 'Bravo:HVA:0'
    assert eot.guardian is None
    assert eot.prob == 0.8
    assert eot.success is True

"""Scoring functions and default weights for candidate line rating

FOW_WEIGHT + FRC_WEIGHT + GEO_WEIGHT + BEAR_WEIGHT should always be `1`.

The result of the scoring functions will be floats from 0.0 to 1.0,
with `1.0` being an exact match and 0.0 being a non-match."""

from logging import debug
from openlr import FRC, FOW, LocationReferencePoint
from ..maps.wgs84 import distance, Coordinates, extrapolate
from .path_math import coords, PointOnLine, compute_bearing, simple_frechet
from .configuration import Config


def score_frc(wanted: FRC, actual: FRC) -> float:
    "Return a score for a FRC value"
    return 1.0 - abs(actual - wanted) / 7

def angle_difference(angle1: float, angle2: float) -> float:
    """The difference of two angle values.

    Args:
        angle1, angle2:
            The values are expected in degrees.
    Returns:
        A value in the range [-180.0, 180.0]"""
    return (abs(angle1 - angle2) + 180) % 360 - 180

def score_angle_difference(angle1: float, angle2: float) -> float:
    """Helper for `score_bearing` which scores the angle difference.

    Args:
        angle1, angle2: angles, in degrees.
    Returns:
        The similarity of angle1 and angle2, from 0.0 (180° difference) to 1.0 (0° difference)
    """
    difference = angle_difference(angle1, angle2)
    return 1 - abs(difference) / 180


def score_shape(wanted: LocationReferencePoint, candidate: PointOnLine, config: Config) -> float:
    "Computes a geo/shape score for a candidate"
    max_distance = config.search_radius * 2 * config.bear_dist
    expected_start = Coordinates(wanted.lon, wanted.lat)
    expected_end = extrapolate(expected_start, max_distance, wanted.angle)
    distance = simple_frechet(
        (expected_start, expected_end),
        (candidate.position, candidate.line.end_node.coordinates)
    )
    return 1.0 - distance / config.search_radius

def score_lrp_candidate(
        wanted: LocationReferencePoint,
        candidate: PointOnLine, config: Config, is_last_lrp: bool
) -> float:
    """Scores the candidate (line) for the LRP.

    This is the average of fow, frc, geo and bearing score."""
    debug(f"scoring {candidate} with config {config}")
    shape_score = config.shape_weight * score_shape(wanted, candidate, config)
    fow_score = config.fow_weight * config.fow_standin_score[wanted.fow][candidate.line.fow]
    frc_score = config.frc_weight * score_frc(wanted.frc, candidate.line.frc)
    score = fow_score + frc_score + shape_score
    debug(f"Score: shape {shape_score} + fow {fow_score} + frc {frc_score} "
          f"= {score}")
    return score

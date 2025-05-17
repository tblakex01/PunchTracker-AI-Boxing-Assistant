from utils.punch_counter import PunchCounter


def test_classify_cross():
    pc = PunchCounter()
    keypoints = {
        'right_wrist': (1.1, 0.0, 1.0),
        'right_elbow': (0.5, 0.0, 1.0),
        'right_shoulder': (0.0, 0.0, 1.0),
        'left_shoulder': (-0.2, 0.0, 1.0),
    }
    punch_type = pc._classify_punch_type(keypoints, 'right', velocity=60)
    assert punch_type == pc.CROSS


def test_classify_uppercut():
    pc = PunchCounter()
    keypoints = {
        'left_wrist': (0.0, -1.1, 1.0),
        'left_elbow': (0.0, -0.5, 1.0),
        'left_shoulder': (0.0, 0.0, 1.0),
        'right_shoulder': (0.5, 0.0, 1.0),
    }
    punch_type = pc._classify_punch_type(keypoints, 'left', velocity=60)
    assert punch_type == pc.UPPERCUT

# Copyright (c) OpenMMLab. All rights reserved.
import cv2
import numpy as np


def apply_bugeye_effect(img,
                        pose_results,
                        left_eye_index,
                        right_eye_index,
                        kpt_thr=0.5):
    """Apply bug-eye effect.

    Args:
        img (np.ndarray): Image data.
        pose_results (list[dict]): The pose estimation results containing:
            - "bbox" ([K, 4(or 5)]): detection bbox in
                [x1, y1, x2, y2, (score)]
            - "keypoints" ([K,3]): keypoint detection result in [x, y, score]
        left_eye_index (int): Keypoint index of left eye
        right_eye_index (int): Keypoint index of right eye
        kpt_thr (float): The score threshold of required keypoints.
    """

    xx, yy = np.meshgrid(np.arange(img.shape[1]), np.arange(img.shape[0]))
    xx = xx.astype(np.float32)
    yy = yy.astype(np.float32)

    for pose in pose_results:
        bbox = pose['bbox']
        kpts = pose['keypoints']

        if kpts[left_eye_index, 2] < kpt_thr or kpts[right_eye_index,
                                                     2] < kpt_thr:
            continue

        kpt_leye = kpts[left_eye_index, :2]
        kpt_reye = kpts[right_eye_index, :2]
        for xc, yc in [kpt_leye, kpt_reye]:

            # distortion parameters
            k1 = 0.001
            epe = 1e-5

            scale = (bbox[2] - bbox[0])**2 + (bbox[3] - bbox[1])**2
            r2 = ((xx - xc)**2 + (yy - yc)**2)
            r2 = (r2 + epe) / scale  # normalized by bbox scale

            xx = (xx - xc) / (1 + k1 / r2) + xc
            yy = (yy - yc) / (1 + k1 / r2) + yc

        img = cv2.remap(
            img,
            xx,
            yy,
            interpolation=cv2.INTER_AREA,
            borderMode=cv2.BORDER_REPLICATE)
    return img


def apply_sunglasses_effect(img,
                            pose_results,
                            sunglasses_img,
                            left_eye_index,
                            right_eye_index,
                            kpt_thr=0.5):
    """Apply sunglasses effect.

    Args:
        img (np.ndarray): Image data.
        pose_results (list[dict]): The pose estimation results containing:
            - "keypoints" ([K,3]): keypoint detection result in [x, y, score]
        sunglasses_img (np.ndarray): Sunglasses image with white background.
        left_eye_index (int): Keypoint index of left eye
        right_eye_index (int): Keypoint index of right eye
        kpt_thr (float): The score threshold of required keypoints.
    """

    hm, wm = sunglasses_img.shape[:2]
    # anchor points in the sunglasses mask
    pts_src = np.array([[0.3 * wm, 0.3 * hm], [0.3 * wm, 0.7 * hm],
                        [0.7 * wm, 0.3 * hm], [0.7 * wm, 0.7 * hm]],
                       dtype=np.float32)

    for pose in pose_results:
        kpts = pose['keypoints']

        if kpts[left_eye_index, 2] < kpt_thr or kpts[right_eye_index,
                                                     2] < kpt_thr:
            continue

        kpt_leye = kpts[left_eye_index, :2]
        kpt_reye = kpts[right_eye_index, :2]
        # orthogonal vector to the left-to-right eyes
        vo = 0.5 * (kpt_reye - kpt_leye)[::-1] * [-1, 1]

        # anchor points in the image by eye positions
        pts_tar = np.vstack(
            [kpt_reye + vo, kpt_reye - vo, kpt_leye + vo, kpt_leye - vo])

        h_mat, _ = cv2.findHomography(pts_src, pts_tar)
        patch = cv2.warpPerspective(
            sunglasses_img,
            h_mat,
            dsize=(img.shape[1], img.shape[0]),
            borderValue=(255, 255, 255))
        #  mask the white background area in the patch with a threshold 200
        mask = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        mask = (mask < 200).astype(np.uint8)
        img = cv2.copyTo(patch, mask, img)

    return img


def apply_hat_effect(img,
                     pose_results,
                     hat_img,
                     left_eye_index,
                     right_eye_index,
                     kpt_thr=0.5):
    """Apply hat effect.
    Args:
        img (np.ndarray): Image data.
        pose_results (list[dict]): The pose estimation results containing:
            - "keypoints" ([K,3]): keypoint detection result in [x, y, score]
        hat_img (np.ndarray): Hat image with white alpha channel.
        left_eye_index (int): Keypoint index of left eye
        right_eye_index (int): Keypoint index of right eye
        kpt_thr (float): The score threshold of required keypoints.
    """
    img_orig = img.copy()

    img = img_orig.copy()
    hm, wm = hat_img.shape[:2]
    # anchor points in the sunglasses mask
    a = 0.3
    b = 0.7
    pts_src = np.array([[a * wm, a * hm], [a * wm, b * hm], [b * wm, a * hm],
                        [b * wm, b * hm]],
                       dtype=np.float32)

    for pose in pose_results:
        kpts = pose['keypoints']

        if kpts[left_eye_index, 2] < kpt_thr or \
                kpts[right_eye_index, 2] < kpt_thr:
            continue

        kpt_leye = kpts[left_eye_index, :2]
        kpt_reye = kpts[right_eye_index, :2]
        # orthogonal vector to the left-to-right eyes
        vo = 0.5 * (kpt_reye - kpt_leye)[::-1] * [-1, 1]
        veye = 0.5 * (kpt_reye - kpt_leye)

        # anchor points in the image by eye positions
        pts_tar = np.vstack([
            kpt_reye + 1 * veye + 5 * vo, kpt_reye + 1 * veye + 1 * vo,
            kpt_leye - 1 * veye + 5 * vo, kpt_leye - 1 * veye + 1 * vo
        ])

        h_mat, _ = cv2.findHomography(pts_src, pts_tar)
        patch = cv2.warpPerspective(
            hat_img,
            h_mat,
            dsize=(img.shape[1], img.shape[0]),
            borderValue=(255, 255, 255))
        #  mask the white background area in the patch with a threshold 200
        mask = (patch[:, :, -1] > 128)
        patch = patch[:, :, :-1]
        mask = mask * (cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY) > 30)
        mask = mask.astype(np.uint8)

        img = cv2.copyTo(patch, mask, img)
    return img


def apply_firecracker_effect(img,
                             pose_results,
                             firecracker_img,
                             left_wrist_idx,
                             right_wrist_idx,
                             kpt_thr=0.5):
    """Apply firecracker effect.
    Args:
        img (np.ndarray): Image data.
        pose_results (list[dict]): The pose estimation results containing:
            - "keypoints" ([K,3]): keypoint detection result in [x, y, score]
        firecracker_img (np.ndarray): Firecracker image with white background.
        left_wrist_idx (int): Keypoint index of left wrist
        right_wrist_idx (int): Keypoint index of right wrist
        kpt_thr (float): The score threshold of required keypoints.
    """

    hm, wm = firecracker_img.shape[:2]
    # anchor points in the firecracker mask
    pts_src = np.array([[0. * wm, 0. * hm], [0. * wm, 1. * hm],
                        [1. * wm, 0. * hm], [1. * wm, 1. * hm]],
                       dtype=np.float32)

    h, w = img.shape[:2]
    h_tar = h / 3
    w_tar = h_tar / hm * wm

    for pose in pose_results:
        kpts = pose['keypoints']

        if kpts[left_wrist_idx, 2] > kpt_thr:
            kpt_lwrist = kpts[left_wrist_idx, :2]
            # anchor points in the image by eye positions
            pts_tar = np.vstack([
                kpt_lwrist - [w_tar / 2, 0], kpt_lwrist - [w_tar / 2, -h_tar],
                kpt_lwrist + [w_tar / 2, 0], kpt_lwrist + [w_tar / 2, h_tar]
            ])

            h_mat, _ = cv2.findHomography(pts_src, pts_tar)
            patch = cv2.warpPerspective(
                firecracker_img,
                h_mat,
                dsize=(img.shape[1], img.shape[0]),
                borderValue=(255, 255, 255))
            #  mask the white background area in the patch with a threshold 200
            mask = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
            mask = (mask < 240).astype(np.uint8)
            img = cv2.copyTo(patch, mask, img)

        if kpts[right_wrist_idx, 2] > kpt_thr:
            kpt_rwrist = kpts[right_wrist_idx, :2]

            # anchor points in the image by eye positions
            pts_tar = np.vstack([
                kpt_rwrist - [w_tar / 2, 0], kpt_rwrist - [w_tar / 2, -h_tar],
                kpt_rwrist + [w_tar / 2, 0], kpt_rwrist + [w_tar / 2, h_tar]
            ])

            h_mat, _ = cv2.findHomography(pts_src, pts_tar)
            patch = cv2.warpPerspective(
                firecracker_img,
                h_mat,
                dsize=(img.shape[1], img.shape[0]),
                borderValue=(255, 255, 255))
            #  mask the white background area in the patch with a threshold 200
            mask = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
            mask = (mask < 240).astype(np.uint8)
            img = cv2.copyTo(patch, mask, img)

    return img

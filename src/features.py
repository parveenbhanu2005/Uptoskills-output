import numpy as np
import config

def extract_pedestrian_features(tracked_pedestrians, frame_width=1280, frame_height=720):
    """
    Extract spatial, motion, and crowd density features for tracked pedestrians.
    
    Returns:
        dict containing:
            - positions: list of (x, y) bottom-center coordinates
            - velocities: list of (vx, vy) vectors
            - speeds: list of float speed magnitudes
            - directions: list of float angles in radians
            - global_density: pedestrians per 10,000 sq pixels
            - local_densities: list of local density values per pedestrian
            - distance_matrix: pairwise spatial distance matrix (N x N)
            - velocity_similarity_matrix: pairwise direction similarity matrix (N x N)
    """
    num_peds = len(tracked_pedestrians)
    
    if num_peds == 0:
        return {
            'positions': np.empty((0, 2)),
            'velocities': np.empty((0, 2)),
            'speeds': np.array([]),
            'directions': np.array([]),
            'global_density': 0.0,
            'local_densities': np.array([]),
            'distance_matrix': np.empty((0, 0)),
            'velocity_similarity_matrix': np.empty((0, 0))
        }

    positions = np.array([ped['bottom_center'] for ped in tracked_pedestrians], dtype=np.float32)
    velocities = np.array([(ped['vx'], ped['vy']) for ped in tracked_pedestrians], dtype=np.float32)
    
    speeds = np.linalg.norm(velocities, axis=1)
    directions = np.arctan2(velocities[:, 1], velocities[:, 0])

    # Global spatial density (pedestrians per 100x100 pixel area)
    total_area = frame_width * frame_height
    global_density = (num_peds / float(total_area)) * 10000.0

    # Pairwise Spatial Distances
    diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]  # N x N x 2
    distance_matrix = np.linalg.norm(diff, axis=2)                   # N x N

    # Local Density (Inverse average distance to nearest 3 neighbors)
    local_densities = np.zeros(num_peds, dtype=np.float32)
    if num_peds > 1:
        sorted_dists = np.sort(distance_matrix, axis=1)
        k = min(3, num_peds - 1)
        k_nearest_avg = np.mean(sorted_dists[:, 1:k+1], axis=1)
        local_densities = 100.0 / (k_nearest_avg + 1e-5)

    # Velocity Similarity Matrix (Cosine similarity of velocity vectors)
    norm_vels = velocities / (np.linalg.norm(velocities, axis=1, keepdims=True) + 1e-5)
    velocity_similarity_matrix = np.dot(norm_vels, norm_vels.T)
    # Clamp to [-1, 1]
    velocity_similarity_matrix = np.clip(velocity_similarity_matrix, -1.0, 1.0)

    return {
        'positions': positions,
        'velocities': velocities,
        'speeds': speeds,
        'directions': directions,
        'global_density': global_density,
        'local_densities': local_densities,
        'distance_matrix': distance_matrix,
        'velocity_similarity_matrix': velocity_similarity_matrix
    }

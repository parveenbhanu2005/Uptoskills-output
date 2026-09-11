import numpy as np
from sklearn.cluster import DBSCAN
import config

class GroupTracker:
    def __init__(self, group_id_num):
        self.group_id_num = group_id_num
        self.group_id = f"G{group_id_num}"
        self.member_track_ids = set()
        self.consecutive_stable_frames = 0
        self.is_stable = False
        self.creation_frame = 0
        self.last_seen_frame = 0
        self.center_x = 0.0
        self.center_y = 0.0

    def update(self, member_track_ids, current_frame, center_x, center_y):
        # Calculate overlap with previous membership
        if len(self.member_track_ids) > 0:
            intersection = len(self.member_track_ids.intersection(member_track_ids))
            union = len(self.member_track_ids.union(member_track_ids))
            jaccard = intersection / float(union) if union > 0 else 0.0
            
            if jaccard >= 0.5:
                self.consecutive_stable_frames += 1
            else:
                # Reset counter if membership changed drastically
                self.consecutive_stable_frames = max(1, self.consecutive_stable_frames - 1)
        else:
            self.consecutive_stable_frames = 1

        self.member_track_ids = set(member_track_ids)
        self.last_seen_frame = current_frame
        self.center_x = center_x
        self.center_y = center_y

        if self.consecutive_stable_frames >= config.GROUP_STABILITY_FRAMES:
            self.is_stable = True


class GroupDetector:
    def __init__(self, eps=config.GROUP_DISTANCE_THRESHOLD, velocity_weight=config.VELOCITY_WEIGHT):
        """
        Pedestrian Group Formation Detector using Spatial & Trajectory DBSCAN.
        """
        self.eps = eps
        self.velocity_weight = velocity_weight
        self.next_group_num = 1
        self.active_groups = {}  # group_id str -> GroupTracker object

    def detect_groups(self, tracked_pedestrians, features, frame_number):
        """
        Form pedestrian groups based on spatial proximity & motion vector similarity.
        
        Returns:
            list of dict: Active group objects containing:
                - 'group_id': str (e.g. 'G1')
                - 'member_track_ids': list of int
                - 'pedestrians': list of pedestrian dicts
                - 'is_stable': bool
                - 'center': (x, y)
                - 'consecutive_stable_frames': int
        """
        num_peds = len(tracked_pedestrians)
        if num_peds < config.MIN_GROUP_SIZE:
            # Not enough pedestrians to form a group
            return []

        dist_matrix = features['distance_matrix']
        vel_sim_matrix = features['velocity_similarity_matrix']
        speeds = features['speeds']

        # Construct combined distance matrix
        effective_dist_matrix = np.zeros_like(dist_matrix)
        for i in range(num_peds):
            for j in range(num_peds):
                if i == j:
                    effective_dist_matrix[i, j] = 0.0
                else:
                    spatial_d = dist_matrix[i, j]
                    # Incorporate velocity similarity if both pedestrians are moving
                    if speeds[i] > 0.5 and speeds[j] > 0.5:
                        motion_penalty = (1.0 - vel_sim_matrix[i, j]) * self.velocity_weight
                    else:
                        motion_penalty = 0.0
                    effective_dist_matrix[i, j] = spatial_d + motion_penalty

        # DBSCAN clustering with precomputed effective distance
        db = DBSCAN(eps=self.eps, min_samples=config.MIN_GROUP_SIZE, metric='precomputed')
        cluster_labels = db.fit_predict(effective_dist_matrix)

        # Map cluster labels to track_ids
        raw_clusters = {}
        for idx, label in enumerate(cluster_labels):
            if label != -1:  # -1 represents noise/un-grouped individuals
                if label not in raw_clusters:
                    raw_clusters[label] = []
                raw_clusters[label].append(idx)

        # Process each raw cluster into tracked groups
        current_frame_groups = []
        updated_group_ids = set()

        for label, member_indices in raw_clusters.items():
            cluster_track_ids = set([tracked_pedestrians[idx]['track_id'] for idx in member_indices])
            
            # Compute centroid of cluster
            cluster_peds = [tracked_pedestrians[idx] for idx in member_indices]
            cx = float(np.mean([p['bottom_center'][0] for p in cluster_peds]))
            cy = float(np.mean([p['bottom_center'][1] for p in cluster_peds]))

            # Match cluster to existing active group using Jaccard index
            best_match_id = None
            best_jaccard = 0.0

            for gid, grp_obj in self.active_groups.items():
                if gid in updated_group_ids:
                    continue
                intersection = len(grp_obj.member_track_ids.intersection(cluster_track_ids))
                union = len(grp_obj.member_track_ids.union(cluster_track_ids))
                jaccard = intersection / float(union) if union > 0 else 0.0

                if jaccard > best_jaccard and jaccard >= config.GROUP_JACCARD_THRESHOLD:
                    best_jaccard = jaccard
                    best_match_id = gid

            if best_match_id is not None:
                # Existing group matched
                grp_obj = self.active_groups[best_match_id]
                grp_obj.update(cluster_track_ids, frame_number, cx, cy)
                updated_group_ids.add(best_match_id)
            else:
                # Create new group
                grp_obj = GroupTracker(self.next_group_num)
                self.next_group_num += 1
                grp_obj.creation_frame = frame_number
                grp_obj.update(cluster_track_ids, frame_number, cx, cy)
                self.active_groups[grp_obj.group_id] = grp_obj
                updated_group_ids.add(grp_obj.group_id)

            current_frame_groups.append({
                'group_id': grp_obj.group_id,
                'member_track_ids': list(cluster_track_ids),
                'pedestrians': cluster_peds,
                'is_stable': grp_obj.is_stable,
                'center': (cx, cy),
                'consecutive_stable_frames': grp_obj.consecutive_stable_frames
            })

        # Remove stale groups not seen in recent frames
        stale_ids = [gid for gid, grp in self.active_groups.items() if frame_number - grp.last_seen_frame > 15]
        for gid in stale_ids:
            del self.active_groups[gid]

        return current_frame_groups

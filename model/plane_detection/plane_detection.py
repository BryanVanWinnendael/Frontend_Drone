import open3d as o3d
from model.plane_detection.color_generator import GenerateColors
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from model.model_utils import GetDefaulftParameters, GetValidClusterStrategies

def SaveResult(planes):
    pcds = o3d.geometry.PointCloud()
    for plane in planes:
        pcds += plane

    o3d.io.write_point_cloud("data/results/result-classified.ply", pcds)

def SegmentPlanes(pcd, cluster=None, parameters=GetDefaulftParameters()):
    # Prepare necessary variables
    points = np.asarray(pcd.points)
    planes = []
    N = len(points)
    target = points.copy()
    count = 0
    max_loops = parameters["max_loops"]

    print(f"Starting with {N} points")

    # Because infinite loops are possible we limit the max amount of loops
    # Loop until the minimum ratio of points is reached
    while count < (1 - parameters["min_ratio"]) * N and max_loops > 0:
        # Convert back to open3d point cloud
        cloud = o3d.geometry.PointCloud()
        cloud.points = o3d.utility.Vector3dVector(target)

        # Segment the plane
        inliers, mask = cloud.segment_plane(distance_threshold=parameters["treshold"], ransac_n=3, num_iterations=parameters["iterations"])

        # Extract the plane
        plane = cloud.select_by_index(mask)

        if cluster != None and cluster in GetValidClusterStrategies():
            inlier_points = np.asarray(plane.points)

            # Remaining clusters
            remaining_clusters = []

            if cluster == "DBSCAN":
                # Perform DBSCAN clustering on the points
                labels = np.array(plane.cluster_dbscan(eps=0.1, min_points=20, print_progress=True))
            elif cluster == "Agglomerative":
                # Perform agglomerative clustering on the points
                labels = AgglomerativeClustering(n_clusters=3).fit_predict(inlier_points)
            
            # Extract points for each cluster
            for label in np.unique(labels):
                # Get the points for this cluster
                cluster_points = inlier_points[labels == label]

                print(f"Found cluster with {len(cluster_points)} points")

                if len(cluster_points) >= parameters["min_points"]:
                    # Convert points to Open3D point cloud
                    cluster_pcd = o3d.geometry.PointCloud()
                    cluster_pcd.points = o3d.utility.Vector3dVector(cluster_points)

                    # Add the cluster point cloud to the list of planes
                    planes.append(cluster_pcd)

                    # Update the count
                    count += len(cluster_points)
                else:
                    # Put the points back into the target
                    print("Not enough points to be a plane, adding points back to target")
                    remaining_clusters.append(cluster_points)
        else:
            # Add the plane to the list
            planes.append(plane)

            # Update the count
            count += len(mask)

        # Remove the plane from the target
        target = np.delete(target, mask, axis=0)

        # Add the remaining points back to the target
        if cluster != "None":
            for remaining_cluster in remaining_clusters:
                target = np.concatenate((target, remaining_cluster), axis=0)

        max_loops -= 1

    # Check if all loops were used and if so add the remaining points to a plane
    if max_loops <= 0 and len(target) >= parameters["min_points"]:
        print("Adding remaining points to a plane")
        plane = o3d.geometry.PointCloud()
        plane.points = o3d.utility.Vector3dVector(target)
        planes.append(plane)


    print(f"Found {len(planes)} planes")

    return planes

# Detect planes solely based on RANSAC
def DetectPlanes(filename, waitingScreen, cluster=None, parameters=GetDefaulftParameters()):
    # Load in point cloud
    print("Loading point cloud...")
    waitingScreen.progress.emit("Loading point cloud...")
    pcd = o3d.io.read_point_cloud(filename)

    # Preprocess the point cloud
    print("Preprocessing point cloud...")
    pcd = pcd.voxel_down_sample(voxel_size=parameters["voxel_size"])
    pcd, mask = pcd.remove_statistical_outlier(nb_neighbors=parameters["neighbours"], std_ratio=parameters["min_std_ratio"])
    # This was removed for now because it was causing the point cloud to be too small
    # pcd, mask = pcd.remove_radius_outlier(nb_points=16, radius=0.05)

    # Segment the planes
    print("Segmenting planes...")
    waitingScreen.progress.emit("Segmenting planes...")
    planes = SegmentPlanes(pcd, cluster=cluster, parameters=parameters)

    # Generate range of colors
    colors = GenerateColors(len(planes))

    print("Planes detected: " + str(len(planes)))
    waitingScreen.progress.emit("Planes detected: " + str(len(planes)))

    # Loop through each plane and save it to a file
    print("Saving planes...")
    waitingScreen.progress.emit("Saving planes...")
    for i, plane in enumerate(planes):
        r = colors[i][0] / 255
        g = colors[i][1] / 255
        b = colors[i][2] / 255

        plane.paint_uniform_color([r, g, b])
        o3d.io.write_point_cloud("data/planes/plane_" + str(i + 1) + ".ply", plane)
    
    # Save the result
    print("Saving result...")
    waitingScreen.progress.emit("Saving result...")
    SaveResult(planes)
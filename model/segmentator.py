from model.plane_detection.plane_detection import DetectPlanes
from model.plane_detection.plane_to_mesh import PlanesToMeshes
from model.plane_detection.surface_calculator import CalculateSurfaces
from model.view_data import ViewPointCloud, ViewMesh, ViewResult

class Segmentator:
    def __init__(self):
        pass

    def segment(self, filename):
        DetectPlanes(filename)
        PlanesToMeshes()
        CalculateSurfaces()
        #ViewResult()

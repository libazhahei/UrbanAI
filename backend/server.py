from logging.handlers import RotatingFileHandler
from flask import Flask, request, Response, stream_with_context, make_response
from flask_cors import CORS, cross_origin
from flask_restx import Api, Resource
from flask_restx import fields, inputs, reqparse, Namespace
# from flask_restx import
import json
from src.database.database import database
from src.loaders.TifLoader import TifLoader
# from src.resources.resource import load_from_meshes, load_from_pcds, process_pcd, process_mesh
from src.fetchers.ResourceFetcher import MeshResourceFetcher, PcdResourceFetcher, TreeModelResourceFetcher
from src.fetchers.RegionDataFetcher import RegionDataFetcher
from src.fetchers.FetchersConsts import ResourceType, ResourceAttr
from src.fetchers.TifRegionFetcher import TifRegionFetcher
from src.fetchers.TifFetcher import TifFetcher
import time
from src.always_on.CacheClear import CaCheClear, RegionsClear
from src.always_on.AlwaysOnLauncher import Launcher
from datetime import timedelta
from src.exceptions.ServerExceptions import InvalidResourceId, InvalidRequestType, InvalidInput, LargeSelectedArea, InvalidAuth, ResourceNotFound
import logging
import os
import concurrent
from src.fetchers.GoogleMapFetcher import StatelliteFetcher
from src.predictors.trees import tree_predictor
from src.predictors.roads import road_predictor
from src.predictors.buildings import building_predictor
import numpy as np
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler("server.log")  ])
logger = logging.getLogger(__name__)
CLEAR_CACHE = hash(time.time())

PORT = 9999
app = Flask(__name__)
CORS(app, origins="*")
handler = RotatingFileHandler('users.log', backupCount=1)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
app.logger.addHandler(handler)

API = Api(app)


NS1 = Namespace(name="API - Topographic mesh viewer", description="Api for topographic mesh viewer", path="/v1/api")
NS2 = Namespace(name="API - Satellite image detection", description="Api for satellite image detection", path="/v1/api")
API.add_namespace(NS1)
API.add_namespace(NS2)

resource_parser = reqparse.RequestParser()
resource_parser.add_argument('type', type=str, choices=["mesh", "pcb", "trees"], required=True)
resource_parser.add_argument('id', type=str, required=True)

coord_model = API.model(
    "CoordModel",
    {
        "latitude" : fields.Float(required=True, default=-32.5),
        "longitude" : fields.Float(required=True, default=147.0)
    }
)
# region_mesh_parser.add_argument('data', required=True)

region_mesh_model = NS1.model(
    "RegionMeshModel",
    {
        "type" : fields.String(required=True, enum=["polygon", "circle", "map"]),
        "data" : fields.List(fields.Raw, required=True, default=[{"latitude" : -32.5, "longitude" : 147.0}, {"latitude" : -33.5, "longitude" : 147.5}])
    }
)

detect_model = NS2.model(
    "DetectModel",
    {
        "data" : fields.List(fields.Nested(coord_model), required=True, default=[{"latitude" : -33.8460, "longitude" : 150.9762}])
    }
)
import datetime
request_counts = {}
max_record_time = 100

def record_user(request):
    """
    Records the user's request count and access information based on their IP address.

    Args:
        request: The request object containing information about the user's request.

    Returns:
        None
    """
    ip_address = request.remote_addr
    now = datetime.datetime.now()
    # increment request count for IP address
    if ip_address in request_counts:
        request_counts[ip_address]['last_access_time'] = now
        request_counts[ip_address]['access_days'].add(now.date())
    else:
        request_counts[ip_address] = {
            'last_access_time': now,
            'access_days': {now.date()}
        }
    # log request count for IP address
    app.logger.info(f'Request count for {ip_address}: {request_counts[ip_address]}')
    if len(request_counts) > max_record_time:
        app.logger.info(f'summery every 30 requests {ip_address}: {request_counts[ip_address]}')
        

@API.route(f"/v1/get/key/{CLEAR_CACHE}")
class MapKey(Resource):
    """
    Represents a resource for retrieving the key for clearing cache.
    """

    @API.doc(description="get the key for clear cache in local network, i.e. 127.0.0.1")
    def get(self):
        """
        Retrieves the key for clearing cache in the local network.

        Returns:
            dict: A dictionary containing the key for clearing cache.

        Raises:
            InvalidAuth: If the request is not from the local network.
        """
        record_user(request)
        if request.remote_addr == "127.0.0.1":
            app.logger.info(f'Request KEY for {request.remote_addr}')
            return {"key":  CLEAR_CACHE}
        else:
            raise InvalidAuth("You have no permission.")
    
    @API.doc(description="get the key for clear cache with password")
    def post(self):
        """
        Retrieves the key for clearing cache with a password.

        Returns:
            dict: A dictionary containing the key for clearing cache.

        Raises:
            InvalidAuth: If the password is incorrect.
        """
        record_user(request)
        data = request.json
        if data['password'] == '__URBANAI__PASSWORD__':
            return {"key":  CLEAR_CACHE}
        else:
            raise InvalidAuth("You have no permission.")

@API.route("/v1/clear/log")
class ClearLog(Resource):
    def delete(self):
        """
        Deletes the log entries based on the provided authentication key.

        Args:
            None

        Returns:
            A dictionary containing the success message if the authentication key is valid.

        Raises:
            InvalidAuth: If the provided authentication key is invalid.
        """
        data = request.json
        if data['key'] == CLEAR_CACHE:
            database.clear_cache()
            database.report()
            # raise
            return {"message" : "Successed"}, 200
        else:
            raise InvalidAuth("You have no premission.")
        
        
@API.route("/v1/clear/cache")
class ClearCache(Resource):
    def delete(self):
        """
        Clears the cache based on the provided key.

        Returns:
            A dictionary with a success message and HTTP status code 200 if the cache is cleared successfully.
        
        Raises:
            InvalidAuth: If the provided key does not match the expected value.
        """
        data = request.json
        if data['key'] == CLEAR_CACHE:
            database.clear_cache()
            database.report()
            # raise
            return {"message" : "Successed"}, 200
        else:
            raise InvalidAuth("You have no premission.")
        
@API.route("/v1/clear/regions")
class ClearRegions(Resource):
    def delete(self):
        """
        Deletes regions from the database based on the provided key.

        Returns:
            A dictionary with a success message if the deletion is successful.
            Raises InvalidAuth exception if the provided key is invalid.
        """
        data = request.json
        if data['key'] == CLEAR_CACHE:
            database.clear_regions()
            database.report()
            return {"message" : "Successed"}, 200
        else:
            raise InvalidAuth("You have no premission.")


@API.route("/v1/download")
class V1Download(Resource):
    """
    Represents a resource download endpoint.

    This class handles the download of different types of resources based on the provided resource type and ID.
    """

    @API.doc(description="Download a resource by id")
    @API.expect(resource_parser, validate=True)
    @API.response(200, "Success")
    @API.response(400, "Invalid Input")
    def get(self):
        resource_type = request.args.get("type", "mesh")
        id = request.args.get("id", None)
        tail_name = "txt"
        if resource_type == "mesh":
            fetcher = MeshResourceFetcher()
            path = fetcher.get_pth(ResourceAttr.UNIQUE_ID, id)
            tail_name = "ply"
        elif resource_type == "pcb":
            fetcher = PcdResourceFetcher()
            path = fetcher.get_pth(ResourceAttr.UNIQUE_ID, id)
            tail_name = "pcd"
        elif resource_type == "trees":
            fetcher = TreeModelResourceFetcher()
            path = fetcher.get_pth(ResourceAttr.UNIQUE_ID, id)
            tail_name = "obj"
        elif resource_type == "geojson":
            raise ResourceNotFound("Resource not found.")
        else:
            raise InvalidRequestType(f"Invalid format {resource_type}, expect mesh or pcb.")
        if path is None:
            raise InvalidResourceId(f"Invalid Resource ID {id}, please check the url agagin")
        CHUNK_SIZE = 4096
        def read_file_chunks(url):
            with open(url, 'rb') as fd:
                while 1:
                    buf = fd.read(CHUNK_SIZE)
                    if buf:
                        yield buf
                    else:
                        break
        try:
            return Response(
                stream_with_context(read_file_chunks(path)),
                headers={
                    'Content-Disposition': f'attachment; filename={f"test_download.{tail_name}"}'
                }
            )
        except FileNotFoundError:
            raise ResourceNotFound("Resource not found.")


def phrase_polygon(data):
    """
    Phrases the latitude and longitude coordinates in the given data and returns a list of polygons.

    Args:
        data (list): A list of coordinates.

    Returns:
        list: A list of polygons.

    """
    polygon = []
    for each in data:
        polygon.append(phrase_lat_lon(each))
    return polygon

def phrase_lat_lon(data):
    """
    Convert latitude and longitude values from a dictionary to a list of floats.

    Args:
        data (dict): A dictionary containing 'latitude' and 'longitude' keys.

    Returns:
        list: A list containing the latitude and longitude values as floats.
    """
    return [float(data['latitude']), float(data['longitude'])]

@cross_origin
@NS1.route("/region/mesh")
class V1ApiRegionAdd(Resource):
    @NS1.expect(region_mesh_model, validate=True)
    @NS1.doc(description="Create a region mesh")
    @NS1.response(200, "Success")
    @NS1.response(500, "Invalid Input")
    def post(self):
        """
        Create a region mesh based on the provided data.

        Returns:
            dict: A dictionary containing the download link and details of the created region mesh.
        
        Raises:
            InvalidRequestType: If the provided data is invalid or missing required fields.
        """
        if request.headers.get("Content-Type") == "text/plain":
            data = json.loads(request.data)
        else:
            data = request.json
        print(data)
        try:
            if data['type'] == 'polygon':
                chunk = RegionDataFetcher.create_by_polygon(phrase_polygon(data['data']))
            elif data['type'] == 'circle':
                chunk = RegionDataFetcher.create_by_circle(phrase_lat_lon(data['data']), data['data']['radius'])
            elif data['type'] == 'map':
                chunk = RegionDataFetcher.create_by_polygon(phrase_polygon(data['data']))
            else:
                raise InvalidRequestType(f"Invalid format {data['type']}, expect polygon or circle.")
        except KeyError:
            raise InvalidRequestType("You must include a type with data.")
        except TypeError:
            raise InvalidRequestType("You must include a valid data type.")
        record_user(request)
        if database.in_cache(chunk.to_range_string()):
            print("requested area is in cache")
            data = database.get_cache(chunk.to_range_string())
            chunk = RegionDataFetcher.read_from_database(data['id'])
            downlink = data['download_link']
        else:
            chunk.make_mesh()
            chunk.write_to_database()
            downlink = chunk.make_link(ResourceType.MESH)
            database.put_cache(chunk.to_range_string(), {"id" : chunk.id, "download_link": downlink, "mesh_id": chunk.mesh})
        return {
            "download" : downlink,
            "details" : chunk.to_details()
        }
    # def options(self):

    #     return Response(headers={"Access-Control-Allow-Methods" : "POST,GET,DELETE,OPTIONS"})

@cross_origin
@NS2.route("/region/detect_image")
class V1ApiRegionDetectImage(Resource):
    """
    API resource for detecting trees, buildings, and roads in an image.
    """

    @NS2.expect(detect_model, validate=True)
    @NS2.doc(description="detect trees, buildings, and roads")
    @NS2.response(200, "Success")
    @NS2.response(500, "Invalid Input: Large region")
    @NS2.response(400, "Invalid Input: Invalid type")
    def post(self):
        from src.predictors.utils.resplot import merge_image, encode_image
        if request.headers.get("Content-Type") == "text/plain":
            data = json.loads(request.data)
        else:
            data = request.json
        record_user(request)
        img = StatelliteFetcher.fetch_by_polygon(phrase_polygon(data['data']))
        building = building_predictor.predict_image(img)
        roads = road_predictor.predict_image(img)
        trees = tree_predictor.predict_image(img)
        # Create a 2x2 grid
        retval, buffer = encode_image(merge_image(img, building, roads, trees))
        response = make_response(buffer.tobytes())
        response.headers['Content-Type'] = 'image/png'
        return response



@cross_origin
@NS2.route("/region/detect")
class V1ApiRegionAdd(Resource):
    """
    Represents the API endpoint for adding a region.

    This endpoint detects trees, buildings, and roads in a given region.

    Parameters:
        - data (dict): The data containing the region information.

    Returns:
        A dictionary containing the detected trees, buildings, roads, and other information about the region.
    """

    @NS2.expect(detect_model, validate=True)
    @NS2.doc(description="detect trees, buildings, and roads")
    @NS2.response(200, "Success")
    @NS2.response(500, "Invalid Input: Large region")
    @NS2.response(400, "Invalid Input: Invalid type")
    def post(self):
        if request.headers.get("Content-Type") == "text/plain":
            data = json.loads(request.data)
        else:
            data = request.json
        record_user(request)
        img = StatelliteFetcher.fetch_by_polygon(phrase_polygon(data['data']))
        height, width, _ = img.shape
        response = {
            "building": {},
            "road": {},
            "tree": {},
            "size": {
                "width" : width,
                "height" : height
            },
            "download" : "xxxx/xxxx/xxx"
        }
        building = building_predictor.predict(img)
        roads = road_predictor.predict(img)
        trees, tree_types = tree_predictor.predict(img)
        # with concurrent.futures.ThreadPoolExecutor() as executor:
            # pred_tree_future = executor.submit(building_predictor.predict, img)
            # pred_building_future = executor.submit(tree_predictor.predict, img)
            # pred_road_future = executor.submit(tree_predictor.predict, img)
            # trees, tree_types = pred_tree_future.result()
            # building = pred_building_future.result()
            # roads = pred_road_future.result()
        response['tree'] = {
            "num_trees": len(trees),
            "trees": trees,
            "unique_tree_types": list(tree_types)
        }
        response["building"] = {
            "num_trees": len(building),
            "buildings": building
        }
        response["road"] = {
            "num_road_slice": len(roads),
            "roads": roads
        }
        return response
    

@API.errorhandler
def defaultHandler(err):
    """
    Default error handler for the API.

    Args:
        err: The error object.

    Returns:
        A tuple containing the error response and the HTTP status code.
    """
    print('response', err, type(err))
    response = {
        "name": "System Error",
        "message": str(err),
    }
    logger.exception(err)

    return response, getattr(err, 'code', 400)


def check_cuda():
    """
    Checks if CUDA is available on the computer.
    """
    import torch
    if torch.cuda.is_available():
        print("CUDA is available on your computer.")
    else:
        print("------------------- GPU CHECK ------------------")
        print("Warning: CUDA is not available on your computer.")
        print("Warning: CUDA is not available on your computer.")
        print("Warning: CUDA is not available on your computer.")

if __name__ == "__main__":
    database.start()
    database.report()   
    check_cuda() 
    logger.debug(msg= f"Sensitive Operation Hash Key: {CLEAR_CACHE}")
    print("Sensitive Operation Hash Key:", CLEAR_CACHE)
    app.run(port=PORT, debug=False)
import os
import random

import folder_paths
from aiohttp import web
from server import PromptServer

from .nodes import list_images


@PromptServer.instance.routes.get("/random_image/input_dir")
async def get_input_dir(request):
    subfolder = request.rel_url.query.get("subfolder", "")
    base = folder_paths.get_input_directory()
    full = os.path.join(base, subfolder) if subfolder else base
    return web.json_response({"directory": os.path.realpath(full)})


@PromptServer.instance.routes.get("/random_image/pick")
async def pick_random_image(request):
    directory = request.rel_url.query.get("dir", "")
    if not directory:
        return web.json_response({"error": "missing 'dir' parameter"}, status=400)

    real_dir = os.path.realpath(directory)
    if not os.path.isdir(real_dir):
        return web.json_response({"error": f"not a directory: {directory}"}, status=400)

    files = list_images(real_dir)
    if not files:
        return web.json_response({"error": "no images found"}, status=404)

    chosen = random.choice(files)
    return web.json_response({"filename": chosen})


@PromptServer.instance.routes.get("/random_image/list")
async def list_images_route(request):
    directory = request.rel_url.query.get("dir", "")
    if not directory:
        return web.json_response({"error": "missing 'dir' parameter"}, status=400)

    real_dir = os.path.realpath(directory)
    if not os.path.isdir(real_dir):
        return web.json_response({"error": f"not a directory: {directory}"}, status=400)

    return web.json_response({"files": list_images(real_dir)})


@PromptServer.instance.routes.get("/random_image/view")
async def view_image(request):
    directory = request.rel_url.query.get("dir", "")
    filename = request.rel_url.query.get("filename", "")
    if not directory or not filename:
        return web.json_response({"error": "missing 'dir' or 'filename' parameter"}, status=400)

    real_dir = os.path.realpath(directory)
    full_path = os.path.realpath(os.path.join(real_dir, filename))

    # reject any filename that resolves outside the requested directory
    if os.path.commonpath([real_dir, full_path]) != real_dir:
        return web.json_response({"error": "invalid filename"}, status=400)

    if not os.path.isfile(full_path):
        return web.json_response({"error": "file not found"}, status=404)

    return web.FileResponse(full_path)

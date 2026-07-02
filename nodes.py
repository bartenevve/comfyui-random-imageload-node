import hashlib
import os
import random

import numpy as np
import torch
from PIL import Image, ImageOps, ImageSequence

VALID_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


def list_images(directory):
    """Recursively list image files under directory, sorted case-insensitively."""
    files = []
    for root, _dirs, filenames in os.walk(directory):
        for name in filenames:
            if os.path.splitext(name)[1].lower() in VALID_EXTENSIONS:
                rel = os.path.relpath(os.path.join(root, name), directory)
                files.append(rel)
    files.sort(key=str.lower)
    return files


class LoadRandomImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory": ("STRING", {"default": ""}),
                "randomize_on_queue": ("BOOLEAN", {"default": False}),
                "sequential_on_queue": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "filename": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("IMAGE", "MASK", "filename")
    FUNCTION = "load_image"
    CATEGORY = "image"

    def _resolve_filenames(self, files, randomize_on_queue, sequential_on_queue, filename):
        """Returns (chosen, next_filename).

        `chosen` is loaded and sent downstream THIS run. `next_filename` is
        pushed back into the widget after execution, becoming the starting
        point for the NEXT run - the advance always happens after the
        current file has already been output, never before.
        """
        if randomize_on_queue:
            chosen = random.choice(files)
            return chosen, chosen

        if sequential_on_queue:
            # this run outputs whatever is currently selected, regardless of
            # whether it got there by manual pick, random pick, or a
            # previous sequential step
            chosen = filename if filename in files else files[0]
            next_filename = files[(files.index(chosen) + 1) % len(files)]
            return chosen, next_filename

        chosen = filename if (filename and filename in files) else files[0]
        return chosen, chosen

    def load_image(self, directory, randomize_on_queue, sequential_on_queue, filename=""):
        directory = os.path.realpath(directory)
        if not os.path.isdir(directory):
            raise NotADirectoryError(f"Not a directory: {directory}")

        files = list_images(directory)
        if not files:
            raise FileNotFoundError(f"No images found in directory: {directory}")

        chosen, next_filename = self._resolve_filenames(
            files, randomize_on_queue, sequential_on_queue, filename
        )
        image_path = os.path.join(directory, chosen)

        img = Image.open(image_path)

        output_images = []
        output_masks = []
        for frame in ImageSequence.Iterator(img):
            frame = ImageOps.exif_transpose(frame)
            if frame.mode == "I":
                frame = frame.point(lambda i: i * (1 / 255))
            rgb_image = frame.convert("RGB")
            arr = np.array(rgb_image).astype(np.float32) / 255.0
            tensor = torch.from_numpy(arr)[None,]

            if "A" in frame.getbands():
                mask_arr = np.array(frame.getchannel("A")).astype(np.float32) / 255.0
                mask = 1.0 - torch.from_numpy(mask_arr)
            else:
                mask = torch.zeros((frame.height, frame.width), dtype=torch.float32)

            output_images.append(tensor)
            output_masks.append(mask.unsqueeze(0))

        if len(output_images) > 1:
            image_out = torch.cat(output_images, dim=0)
            mask_out = torch.cat(output_masks, dim=0)
        else:
            image_out = output_images[0]
            mask_out = output_masks[0]

        # "ui" is pushed to the frontend as the onExecuted message.
        # `filename` seeds the widget for the NEXT run (advance-after-output);
        # `last_loaded` is what this run actually sent downstream, for preview.
        return {
            "ui": {"filename": [next_filename], "last_loaded": [chosen]},
            "result": (image_out, mask_out, chosen),
        }

    @classmethod
    def IS_CHANGED(cls, directory, randomize_on_queue, sequential_on_queue, filename=""):
        if randomize_on_queue or sequential_on_queue:
            return float("nan")
        return hashlib.sha256(filename.encode("utf-8")).hexdigest()

    @classmethod
    def VALIDATE_INPUTS(cls, directory, randomize_on_queue, sequential_on_queue, filename=""):
        if not directory:
            return "Directory path is empty"
        real_dir = os.path.realpath(directory)
        if not os.path.isdir(real_dir):
            return f"Not a valid directory: {directory}"
        return True


NODE_CLASS_MAPPINGS = {
    "LoadRandomImage": LoadRandomImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadRandomImage": "Load Random Image \U0001f3b2",
}

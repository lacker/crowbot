# Convert the mp3s into spectrograms.
# See:
#   https://github.com/teticio/audio-diffusion
# for the instructions that I am vaguely trying to follow.

import io
import logging
import os
import re

import numpy as np
import pandas as pd
from datasets import Dataset, DatasetDict, Features, Image, Value
from diffusers import Mel
from tqdm.auto import tqdm

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger("audio_to_images")

X_RESOLUTION = 64
Y_RESOLUTION = 64
HOP_LENGTH = 1024
INPUT_DIR = "data/mp3s"
OUTPUT_DIR = "data/spectrograms"
SAMPLE_RATE = 22050
N_FFT = 2048


def main():
    mel = Mel(
        x_res=X_RESOLUTION,
        y_res=Y_RESOLUTION,
        hop_length=HOP_LENGTH,
        sample_rate=SAMPLE_RATE,
        n_fft=N_FFT,
    )
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    audio_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(INPUT_DIR)
        for file in files
        if re.search("\.(mp3|wav|m4a)$", file, re.IGNORECASE)
    ]
    examples = []
    try:
        for audio_file in tqdm(audio_files):
            try:
                mel.load_audio(audio_file)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(e)
                continue
            for slice in range(mel.get_number_of_slices()):
                image = mel.audio_slice_to_image(slice)
                assert (
                    image.width == X_RESOLUTION and image.height == Y_RESOLUTION
                ), "Wrong resolution"
                # skip completely silent slices
                if all(np.frombuffer(image.tobytes(), dtype=np.uint8) == 255):
                    logger.warn(
                        "File %s slice %d is completely silent", audio_file, slice
                    )
                    continue
                with io.BytesIO() as output:
                    image.save(output, format="PNG")
                    bytes = output.getvalue()
                examples.extend(
                    [
                        {
                            "image": {"bytes": bytes},
                            "audio_file": audio_file,
                            "slice": slice,
                        }
                    ]
                )
    except Exception as e:
        print(e)
    finally:
        if len(examples) == 0:
            logger.warn("No valid audio files were found.")
            return
        ds = Dataset.from_pandas(
            pd.DataFrame(examples),
            features=Features(
                {
                    "image": Image(),
                    "audio_file": Value(dtype="string"),
                    "slice": Value(dtype="int16"),
                }
            ),
        )
        dsd = DatasetDict({"train": ds})
        dsd.save_to_disk(os.path.join(OUTPUT_DIR))


if __name__ == "__main__":
    print("Running convert.py")
    main()

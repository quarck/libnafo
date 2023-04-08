import imageio.v3 as iio
import glob
import os
import random
import datetime


class ImageNoisifier:
    def __init__(self, num_randomized_points=100, noise_level=1):
        self.num_randomized_points = num_randomized_points
        self.noise_level = noise_level

        self.random = random.Random()
        self.random.seed(int((datetime.datetime.now() - datetime.datetime(1980, 3, 4)).total_seconds() * 1e9))

    def noisify(self, input_file, output_file=None):
        im = iio.imread(input_file).copy()

        w, h, d = im.shape

        for i in range(self.num_randomized_points):
            x = self.random.randint(1, w-2)
            y = self.random.randint(1, h-2)

            for id in range(d):
                if im[x][y][id] > 127:
                    im[x][y][id] -= self.noise_level
                else:
                    im[x][y][id] += self.noise_level

        if output_file is not None:
            return iio.imwrite(output_file, im)
        else:
            return iio.imwrite("<bytes>", im, extension=".png")


if __name__ == "__main__":
    input_folder = r'C:\Users\User\Downloads'
    output_folder = r"C:\Users\User\Desktop\out"

    imn = ImageNoisifier(100)

    for file in glob.glob(os.path.join(input_folder, '*')):
        f, ext = os.path.splitext(file)
        if ext.lower() not in ['.png', '.jpeg', '.jpg', '.bmp', '.jfif']:
            print("Skipping", file)
            continue
        folder, basename = os.path.split(f)
        imn.noisify(file, os.path.join(output_folder, basename + ".png"))

        r = imn.noisify(file)
        print (file, len(r))

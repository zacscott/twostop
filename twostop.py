
import fire
import math
import matplotlib.pyplot as pyplot
import PIL.ImageTk as ImageTk
import PIL.Image as Image
import rawpy
import tkinter


class TwoStopCLI(object):
	"""
	CLI tool to apply the two stop exposure compensation algorithm.
	"""

	def process(self, *files, expcomp=1.0):
		"""
		Process one or more RAW image files applying the 

		:param expcomp: Exposure compensation in stops.
		"""
		
		# convert exposure compensation into the reciprocal which rawpy accepts
		expcomp = 1.0  # TODO calculate this for stops

		# loop through each of the input images and process them
		for path in files:

			# TODO check if file exists

			image_raw = self._raw_read(path)

			image_array = self._raw_process(
				image_raw,
				expcomp=expcomp
			)

			final_image = self._image_twostop(image_array)

			final_path = "test.png"  # TODO actually base off path
			self._image_output(final_path, final_image)
			
			self._log("Done\n")

		self._log("Done. Processed %d images." % len(files))


	def _raw_read(self, path):

		self._log("Reading RAW file %s." % path)

		image_raw = rawpy.imread(path)

		return image_raw


	def _raw_process(self, image_raw, **kwargs):

		self._log("Post processing RAW image.")

		expcomp = kwargs['expcomp'] if 'expcomp' in kwargs else 1.0

		image_array = image_raw.postprocess(
			output_bps=16,
			half_size=True,
			exp_shift=expcomp,
			use_camera_wb=True,
			fbdd_noise_reduction=rawpy.FBDDNoiseReductionMode.Full,
			median_filter_passes=20,
			exp_preserve_highlights=1.0,
			output_color=rawpy.ColorSpace.sRGB,
			no_auto_bright=True
		)

		return image_array


	def _raw_process_preview(self, image_raw):

		self._log("Post processing RAW preview image.")

		image_array = image_raw.postprocess(
			output_bps=8,
			half_size=True,
			use_camera_wb=True,
			fbdd_noise_reduction=rawpy.FBDDNoiseReductionMode.Full,
			output_color=rawpy.ColorSpace.sRGB,
			no_auto_bright=True
		)

		return image_array


	def _image_twostop(self, rows):

		self._log("Two stop processing.")

		# NOTE expects 16bit image as array 
		#      output 8bit PIL image

		row_first = rows[0]
		height_half = int(math.ceil(len(rows)/2))
		width_half = int(int(len(row_first)/2))

		intense = Image.new(
			'RGB',
			(width_half, height_half),
			0
		)

		for y in range(0, height_half):
			row1 = rows[y*2]
			row2 = rows[y*2+1]

			for x in range(0, width_half):

				pixel1 = row1[x*2]
				pixel2 = row1[x*2+1]
				pixel3 = row2[x*2]
				pixel4 = row2[x*2+1]

				# loop through each subpixel/channel and average over the 4 adjacent pixels
				pixel = []
				for s in range(0, 3):

					subpixel = int(pixel1[s]) + int(pixel2[s]) + int(pixel3[s]) + int(pixel4[s])
					subpixel = subpixel / 256
					subpixel = min(subpixel, 255)

					pixel.append(int(subpixel))

				intense.putpixel((x, y), (pixel[0], pixel[1], pixel[2]))

		return intense


	def _image_output(self, path, image):

		self._log("Rendering to file %s." % path)

		image.save(path)


	def _log(self, message):
		"""Output an info message to the console"""

		print(message)


if __name__ == '__main__':
	fire.Fire(TwoStopCLI)

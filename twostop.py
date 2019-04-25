#!/usr/bin/env python3

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
		
		# convert exposure compensation into the format used by rawpy
		expcomp = 1.0  # TODO calculate this for stops

		# process each of the input images
		for path in files:

			image_raw = self._raw_read(path)

			image_array = self._raw_process(
				image_raw,
				expcomp=expcomp
			)

			image_final = self._image_twostop(image_array)

			final_path = "test.jpg"  # TODO actually base off path

			self._image_output(final_path, image_final)
			
			self._log("%s done.\n" % path)

		self._log("Done, processed %d images." % len(files))


	def preview(self, file, expcomp=1.0):
		"""
		Process one or more RAW image files applying the 

		:param file: The RAW file to preview.
		:param expcomp: Exposure compensation in stops.
		"""
		
		# convert exposure compensation into the reciprocal which rawpy accepts
		expcomp = 1.0  # TODO calculate this for stops

		image_raw = self._raw_read(file)

		# process the preview image
		image_preview_array = self._raw_process_preview(image_raw)
		image_preview = self._image_from_array(image_preview_array)

		# process final/two stop image

		image_array = self._raw_process(
			image_raw,
			expcomp=expcomp
		)

		image_final = self._image_twostop(image_array)

		# display comparison & histogram window to user
		self._image_compare_gui(image_preview, image_final)


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

		self._log("Post processing RAW image preview.")

		image_array = image_raw.postprocess(
			output_bps=8,
			half_size=True,
			use_camera_wb=True,
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


	def _image_from_array(self, image_array):

		self._log("Converting image from array.")		

		image = Image.fromarray(image_array.astype('uint8'))

		return image


	def _image_output(self, path, image):

		self._log("Rendering to file %s." % path)

		image.save(
			path, 
			quality=100, 
			optimize=True, 
			progressive=False
		)


	def _image_compare_gui(self, image_preview, image_final):

		# the width of the preview images
		PREVIEW_WIDTH = 600


		root = tkinter.Tk()
		root.title('Preview')

		# build the historgram window

		histogram = image_final.histogram()

		fig = pyplot.gcf()
		fig.canvas.set_window_title('Histogram')

		pyplot.plot(histogram[0:256], color="#ff0000", alpha=0.5)
		pyplot.plot(histogram[256:512], color="#00ff00", alpha=0.5)
		pyplot.plot(histogram[512:768], color="#0000ff", alpha=0.5)

		# build the comparison tk window

		width, height = image_preview.size
		print("%d x %d" % (width, height))
		scale_ratio = float(PREVIEW_WIDTH) / width
		image_preview = image_preview.resize((PREVIEW_WIDTH, int(height*scale_ratio)))

		image_preview_tk = ImageTk.PhotoImage(image_preview)
		image_preview_panel = tkinter.Label(root, image = image_preview_tk)
		image_preview_panel.pack(side="left", fill="both", expand="yes")

		width, height = image_final.size
		scale_ratio = float(PREVIEW_WIDTH) / width
		image_final = image_final.resize((PREVIEW_WIDTH, int(height*scale_ratio)))

		image_final_tk = ImageTk.PhotoImage(image_final)
		image_final_panel = tkinter.Label(root, image = image_final_tk)
		image_final_panel.pack(side="left", fill="both", expand="yes")

		pyplot.show()
		root.mainloop()


	def _log(self, message):
		"""Output an info message to the console"""

		print(message)


if __name__ == '__main__':
	fire.Fire(TwoStopCLI)

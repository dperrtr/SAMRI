import nipype.interfaces.ants as ants
import os
from nipype.interfaces.fsl import GLM, MELODIC, FAST, BET, MeanImage, FLIRT, ImageMaths, FSLCommand

def structural_per_participant_test(participant, conditions=["","_aF","_cF1","_cF2","_pF"]):
	for i in conditions:
		template = "/home/chymera/NIdata/templates/ds_QBI_chr.nii.gz"
		image_dir = "/home/chymera/NIdata/ofM.dr/preprocessing/generic_work/_subject_condition_{}.ofM{}/_scan_type_T2_TurboRARE/structural_bru2nii/".format(participant,i)
		try:
			for myfile in os.listdir(image_dir):
				if myfile.endswith(".nii"):
					mimage = os.path.join(image_dir,myfile)
		except FileNotFoundError:
			pass
		else:
			n4 = ants.N4BiasFieldCorrection()
			n4.inputs.dimension = 3
			n4.inputs.input_image = mimage
			# correction bias is introduced (along the z-axis) if the following value is set to under 85. This is likely contingent on resolution.
			n4.inputs.bspline_fitting_distance = 95
			n4.inputs.shrink_factor = 2
			n4.inputs.n_iterations = [1000,1000,1000,1000]
			n4.inputs.convergence_threshold = 1e-14
			n4.inputs.output_image = 'ss_n4_{}_ofM{}.nii.gz'.format(participant,i)
			n4_res = n4.run()

			struct_cutoff = ImageMaths()
			struct_cutoff.inputs.op_string = "-thrP 20"
			struct_cutoff.inputs.in_file = n4_res.outputs.output_image
			struct_cutoff_res = struct_cutoff.run()

			struct_BET = BET()
			struct_BET.inputs.mask = True
			struct_BET.inputs.frac = 0.3
			struct_BET.inputs.robust = True
			struct_BET.inputs.in_file = struct_cutoff_res.outputs.out_file
			struct_BET_res = struct_BET.run()

			struct_registration = ants.Registration()
			struct_registration.inputs.fixed_image = template
			struct_registration.inputs.output_transform_prefix = "output_"
			struct_registration.inputs.transforms = ['Affine', 'SyN'] ##
			struct_registration.inputs.transform_parameters = [(1.0,), (1.0, 3.0, 5.0)] ##
			struct_registration.inputs.number_of_iterations = [[4000, 2000, 1000], [100, 100, 100]] #
			struct_registration.inputs.dimension = 3
			struct_registration.inputs.write_composite_transform = True
			struct_registration.inputs.collapse_output_transforms = True
			struct_registration.inputs.initial_moving_transform_com = True
			# Tested on Affine transform: CC takes too long, Demons does not tilt, but moves the slices too far caudally
			struct_registration.inputs.metric = ['GC', 'Mattes']
			struct_registration.inputs.metric_weight = [1, 1]
			struct_registration.inputs.radius_or_number_of_bins = [16, 32] #
			struct_registration.inputs.sampling_strategy = ['Random', None]
			struct_registration.inputs.sampling_percentage = [0.3, 0.3]
			struct_registration.inputs.convergence_threshold = [1.e-11, 1.e-8] #
			struct_registration.inputs.convergence_window_size = [20, 20]
			struct_registration.inputs.smoothing_sigmas = [[4, 2, 1], [4, 2, 1]]
			struct_registration.inputs.sigma_units = ['vox', 'vox']
			struct_registration.inputs.shrink_factors = [[3, 2, 1],[3, 2, 1]]
			struct_registration.inputs.use_estimate_learning_rate_once = [True, True]
			# if the fixed_image is not acquired similarly to the moving_image (e.g. RARE to histological (e.g. AMBMC)) this should be False
			struct_registration.inputs.use_histogram_matching = [False, False]
			struct_registration.inputs.winsorize_lower_quantile = 0.005
			struct_registration.inputs.winsorize_upper_quantile = 0.995
			struct_registration.inputs.args = '--float'
			struct_registration.inputs.num_threads = 4

			struct_registration.inputs.moving_image = struct_BET_res.outputs.out_file
			struct_registration.inputs.output_warped_image = 'ss_{}_ofM{}.nii.gz'.format(participant,i)
			res = struct_registration.run()

def functional_per_participant_test():
	for i in ["","_aF","_cF1","_cF2","_pF"]:
		template = "/home/chymera/NIdata/templates/ds_QBI_chr.nii.gz"
		participant = "4008"
		image_dir = "/home/chymera/NIdata/ofM.dr/preprocessing/generic_work/_subject_condition_{}.ofM{}/_scan_type_7_EPI_CBV/temporal_mean/".format(participant,i)
		try:
			for myfile in os.listdir(image_dir):
				if myfile.endswith(".nii.gz"):
					mimage = os.path.join(image_dir,myfile)
		except FileNotFoundError:
			pass
		else:
			n4 = ants.N4BiasFieldCorrection()
			n4.inputs.dimension = 3
			n4.inputs.input_image = mimage
			n4.inputs.bspline_fitting_distance = 100
			n4.inputs.shrink_factor = 2
			n4.inputs.n_iterations = [200,200,200,200]
			n4.inputs.convergence_threshold = 1e-11
			n4.inputs.output_image = 'n4_{}_ofM{}.nii.gz'.format(participant,i)
			n4_res = n4.run()

			functional_cutoff = ImageMaths()
			functional_cutoff.inputs.op_string = "-thrP 30"
			functional_cutoff.inputs.in_file = n4_res.outputs.output_image
			functional_cutoff_res = functional_cutoff.run()

			functional_BET = BET()
			functional_BET.inputs.mask = True
			functional_BET.inputs.frac = 0.5
			functional_BET.inputs.in_file = functional_cutoff_res.outputs.out_file
			functional_BET_res = functional_BET.run()

			registration = ants.Registration()
			registration.inputs.fixed_image = template
			registration.inputs.output_transform_prefix = "output_"
			registration.inputs.transforms = ['Affine', 'SyN']
			registration.inputs.transform_parameters = [(0.1,), (3.0, 3.0, 5.0)]
			registration.inputs.number_of_iterations = [[10000, 10000, 10000], [100, 100, 100]]
			registration.inputs.dimension = 3
			registration.inputs.write_composite_transform = True
			registration.inputs.collapse_output_transforms = True
			registration.inputs.initial_moving_transform_com = True
			registration.inputs.metric = ['Mattes'] * 2 + [['Mattes', 'CC']]
			registration.inputs.metric_weight = [1] * 2 + [[0.5, 0.5]]
			registration.inputs.radius_or_number_of_bins = [32] * 2 + [[32, 4]]
			registration.inputs.sampling_strategy = ['Regular'] * 2 + [[None, None]]
			registration.inputs.sampling_percentage = [0.3] * 2 + [[None, None]]
			registration.inputs.convergence_threshold = [1.e-8] * 2 + [-0.01]
			registration.inputs.convergence_window_size = [20] * 2 + [5]
			registration.inputs.smoothing_sigmas = [[4, 2, 1]] * 2 + [[1, 0.5, 0]]
			registration.inputs.sigma_units = ['vox'] * 3
			registration.inputs.shrink_factors = [[3, 2, 1]]*2 + [[4, 2, 1]]
			registration.inputs.use_estimate_learning_rate_once = [True] * 3
			registration.inputs.use_histogram_matching = [False] * 2 + [True]
			registration.inputs.winsorize_lower_quantile = 0.005
			registration.inputs.winsorize_upper_quantile = 0.995
			registration.inputs.args = '--float'
			registration.inputs.num_threads = 4
			registration.plugin_args = {'qsub_args': '-pe orte 4', 'sbatch_args': '--mem=6G -c 4'}

			registration.inputs.moving_image = functional_BET_res.outputs.out_file
			registration.inputs.output_warped_image = '{}_ofM{}.nii.gz'.format(participant,i)
			res = registration.run()

def structural_to_functional_per_participant_test(participant, conditions=["","_aF","_cF1","_cF2","_pF"]):
	for i in conditions:
		template = "/home/chymera/NIdata/templates/ds_QBI_chr.nii.gz"
		func_image_dir = "/home/chymera/NIdata/ofM.dr/preprocessing/generic_work/_subject_condition_{}.ofM{}/_scan_type_7_EPI_CBV/temporal_mean/".format(participant,i)
		struct_image_dir = "/home/chymera/NIdata/ofM.dr/preprocessing/generic_work/_subject_condition_{}.ofM{}/_scan_type_T2_TurboRARE/structural_bru2nii/".format(participant,i)
		try:
			for myfile in os.listdir(func_image_dir):
				if myfile.endswith(".nii.gz"):
					func_image = os.path.join(func_image_dir,myfile)
			for myfile in os.listdir(struct_image_dir):
				if myfile.endswith(".nii"):
					struct_image = os.path.join(struct_image_dir,myfile)
		except FileNotFoundError:
			pass
		else:
			n4 = ants.N4BiasFieldCorrection()
			n4.inputs.dimension = 3
			n4.inputs.input_image = struct_image
			n4.inputs.bspline_fitting_distance = 100
			n4.inputs.shrink_factor = 2
			n4.inputs.n_iterations = [200,200,200,200]
			n4.inputs.convergence_threshold = 1e-11
			n4.inputs.output_image = 'n4_{}_ofM{}.nii.gz'.format(participant,i)
			n4_res = n4.run()

			struct_cutoff = ImageMaths()
			struct_cutoff.inputs.op_string = "-thrP 30"
			struct_cutoff.inputs.in_file = n4_res.outputs.output_image
			struct_cutoff_res = struct_cutoff.run()

			struct_BET = BET()
			struct_BET.inputs.mask = True
			struct_BET.inputs.frac = 0.5
			struct_BET.inputs.in_file = struct_cutoff_res.outputs.out_file
			struct_BET_res = struct_BET.run()

			struct_registration = ants.Registration()
			struct_registration.inputs.fixed_image = template
			struct_registration.inputs.output_transform_prefix = "output_"
			struct_registration.inputs.transforms = ['Affine', 'SyN'] ##
			struct_registration.inputs.transform_parameters = [(2.0,), (1.0, 3.0, 5.0)] ##
			struct_registration.inputs.number_of_iterations = [[2000, 500, 2000], [100, 100, 100]] #
			struct_registration.inputs.dimension = 3
			struct_registration.inputs.write_composite_transform = True
			struct_registration.inputs.collapse_output_transforms = True
			struct_registration.inputs.initial_moving_transform_com = True
			struct_registration.inputs.metric = ['Mattes', 'Mattes']
			struct_registration.inputs.metric_weight = [1, 1]
			struct_registration.inputs.radius_or_number_of_bins = [16, 32] #
			struct_registration.inputs.sampling_strategy = ['Random', None]
			struct_registration.inputs.sampling_percentage = [0.3, 0.3]
			struct_registration.inputs.convergence_threshold = [1.e-11, 1.e-8] #
			struct_registration.inputs.convergence_window_size = [20, 20]
			struct_registration.inputs.smoothing_sigmas = [[4, 2, 1], [4, 2, 1]]
			struct_registration.inputs.sigma_units = ['vox', 'vox']
			struct_registration.inputs.shrink_factors = [[3, 2, 1],[3, 2, 1]]
			struct_registration.inputs.use_estimate_learning_rate_once = [True, True]
			# if the fixed_image is not acquired similarly to the moving_image (e.g. RARE to histological (e.g. AMBMC)) this should be False
			struct_registration.inputs.use_histogram_matching = [False, False]
			struct_registration.inputs.winsorize_lower_quantile = 0.005
			struct_registration.inputs.winsorize_upper_quantile = 0.995
			struct_registration.inputs.args = '--float'
			struct_registration.inputs.num_threads = 4

			struct_registration.inputs.moving_image = struct_BET_res.outputs.out_file
			struct_registration_res = struct_registration.run()

			warp = ants.ApplyTransforms()
			warp.inputs.reference_image = template
			warp.inputs.input_image_type = 3
			warp.inputs.interpolation = 'Linear'
			warp.inputs.invert_transform_flags = [False]
			warp.inputs.terminal_output = 'file'
			warp.inputs.output_image = '{}_ofM{}.nii.gz'.format(participant,i)
			warp.num_threads = 4

			warp.inputs.input_image = func_image
			warp.inputs.transforms = struct_registration_res.outputs.composite_transform
			warp.run()

def canonical(participant, conditions=["","_aF","_cF1","_cF2","_pF"]):
	for i in conditions:
		template = "/home/chymera/NIdata/templates/ds_QBI_chr.nii.gz"
		func_image_dir = "/home/chymera/NIdata/ofM.dr/preprocessing/generic_work/_subject_condition_{}.ofM{}/_scan_type_7_EPI_CBV/temporal_mean/".format(participant,i)
		struct_image_dir = "/home/chymera/NIdata/ofM.dr/preprocessing/generic_work/_subject_condition_{}.ofM{}/_scan_type_T2_TurboRARE/structural_bru2nii/".format(participant,i)
		try:
			for myfile in os.listdir(func_image_dir):
				if myfile.endswith(".nii.gz"):
					func_image = os.path.join(func_image_dir,myfile)
			for myfile in os.listdir(struct_image_dir):
				if myfile.endswith(".nii"):
					struct_image = os.path.join(struct_image_dir,myfile)
		except FileNotFoundError:
			pass
		else:
			#struct
			struct_n4 = ants.N4BiasFieldCorrection()
			struct_n4.inputs.dimension = 3
			struct_n4.inputs.input_image = struct_image
			struct_n4.inputs.bspline_fitting_distance = 100
			struct_n4.inputs.shrink_factor = 2
			struct_n4.inputs.n_iterations = [200,200,200,200]
			struct_n4.inputs.convergence_threshold = 1e-11
			struct_n4.inputs.output_image = 's_n4_{}_ofM{}.nii.gz'.format(participant,i)
			struct_n4_res = struct_n4.run()

			struct_cutoff = ImageMaths()
			struct_cutoff.inputs.op_string = "-thrP 30"
			struct_cutoff.inputs.in_file = struct_n4_res.outputs.output_image
			struct_cutoff_res = struct_cutoff.run()

			struct_BET = BET()
			struct_BET.inputs.mask = True
			struct_BET.inputs.frac = 0.5
			struct_BET.inputs.in_file = struct_cutoff_res.outputs.out_file
			struct_BET_res = struct_BET.run()

			struct_registration = ants.Registration()
			struct_registration.inputs.fixed_image = template
			struct_registration.inputs.output_transform_prefix = "struct_"
			struct_registration.inputs.transforms = ['Affine', 'SyN']
			struct_registration.inputs.transform_parameters = [(0.1,), (3.0, 3.0, 5.0)]
			struct_registration.inputs.number_of_iterations = [[10000, 10000, 10000], [100, 100, 100]]
			struct_registration.inputs.dimension = 3
			struct_registration.inputs.write_composite_transform = True
			struct_registration.inputs.collapse_output_transforms = True
			struct_registration.inputs.initial_moving_transform_com = True
			struct_registration.inputs.metric = ['Mattes'] * 2 + [['Mattes', 'CC']]
			struct_registration.inputs.metric_weight = [1] * 2 + [[0.5, 0.5]]
			struct_registration.inputs.radius_or_number_of_bins = [32] * 2 + [[32, 4]]
			struct_registration.inputs.sampling_strategy = ['Regular'] * 2 + [[None, None]]
			struct_registration.inputs.sampling_percentage = [0.3] * 2 + [[None, None]]
			struct_registration.inputs.convergence_threshold = [1.e-8] * 2 + [-0.01]
			struct_registration.inputs.convergence_window_size = [20] * 2 + [5]
			struct_registration.inputs.smoothing_sigmas = [[4, 2, 1]] * 2 + [[1, 0.5, 0]]
			struct_registration.inputs.sigma_units = ['vox'] * 3
			struct_registration.inputs.shrink_factors = [[3, 2, 1]]*2 + [[4, 2, 1]]
			struct_registration.inputs.use_estimate_learning_rate_once = [True] * 3
			struct_registration.inputs.use_histogram_matching = [False] * 2 + [True]
			struct_registration.inputs.winsorize_lower_quantile = 0.005
			struct_registration.inputs.winsorize_upper_quantile = 0.995
			struct_registration.inputs.args = '--float'
			struct_registration.inputs.num_threads = 4

			struct_registration.inputs.moving_image = struct_BET_res.outputs.out_file
			struct_registration.inputs.output_warped_image = 's_{}_ofM{}.nii.gz'.format(participant,i)
			struct_registration_res = struct_registration.run()

			#func
			func_n4 = ants.N4BiasFieldCorrection()
			func_n4.inputs.dimension = 3
			func_n4.inputs.input_image = func_image
			func_n4.inputs.bspline_fitting_distance = 100
			func_n4.inputs.shrink_factor = 2
			func_n4.inputs.n_iterations = [200,200,200,200]
			func_n4.inputs.convergence_threshold = 1e-11
			func_n4.inputs.output_image = 'f_n4_{}_ofM{}.nii.gz'.format(participant,i)
			func_n4_res = func_n4.run()

			func_cutoff = ImageMaths()
			func_cutoff.inputs.op_string = "-thrP 30"
			func_cutoff.inputs.in_file = func_n4_res.outputs.output_image
			func_cutoff_res = func_cutoff.run()

			func_BET = BET()
			func_BET.inputs.mask = True
			func_BET.inputs.frac = 0.5
			func_BET.inputs.in_file = func_cutoff_res.outputs.out_file
			func_BET_res = func_BET.run()

			func_registration = ants.Registration()
			func_registration.inputs.fixed_image = struct_BET_res.outputs.out_file
			func_registration.inputs.output_transform_prefix = "func_"
			func_registration.inputs.transforms = ['Affine', 'SyN']
			func_registration.inputs.transform_parameters = [(0.1,), (3.0, 3.0, 5.0)]
			func_registration.inputs.number_of_iterations = [[10000, 10000, 10000], [100, 100, 100]]
			func_registration.inputs.dimension = 3
			func_registration.inputs.write_composite_transform = True
			func_registration.inputs.collapse_output_transforms = True
			func_registration.inputs.initial_moving_transform_com = True
			func_registration.inputs.metric = ['Mattes'] * 2 + [['Mattes', 'CC']]
			func_registration.inputs.metric_weight = [1] * 2 + [[0.5, 0.5]]
			func_registration.inputs.radius_or_number_of_bins = [32] * 2 + [[32, 4]]
			func_registration.inputs.sampling_strategy = ['Regular'] * 2 + [[None, None]]
			func_registration.inputs.sampling_percentage = [0.3] * 2 + [[None, None]]
			func_registration.inputs.convergence_threshold = [1.e-8] * 2 + [-0.01]
			func_registration.inputs.convergence_window_size = [20] * 2 + [5]
			func_registration.inputs.smoothing_sigmas = [[4, 2, 1]] * 2 + [[1, 0.5, 0]]
			func_registration.inputs.sigma_units = ['vox'] * 3
			func_registration.inputs.shrink_factors = [[3, 2, 1]]*2 + [[4, 2, 1]]
			func_registration.inputs.use_estimate_learning_rate_once = [True] * 3
			func_registration.inputs.use_histogram_matching = [False] * 2 + [True]
			func_registration.inputs.winsorize_lower_quantile = 0.005
			func_registration.inputs.winsorize_upper_quantile = 0.995
			func_registration.inputs.args = '--float'
			func_registration.inputs.num_threads = 4

			# func_registration = ants.Registration()
			# func_registration.inputs.fixed_image = struct_BET_res.outputs.out_file
			# func_registration.inputs.output_transform_prefix = "func_"
			# func_registration.inputs.transforms = ['SyN']
			# func_registration.inputs.transform_parameters = [(2.0, 3.0, 5.0)]
			# func_registration.inputs.number_of_iterations = [[100, 100, 100]]
			# func_registration.inputs.dimension = 3
			# func_registration.inputs.write_composite_transform = True
			# func_registration.inputs.collapse_output_transforms = True
			# func_registration.inputs.initial_moving_transform_com = True
			# func_registration.inputs.metric = [['Mattes', 'CC']]
			# func_registration.inputs.metric_weight = [[0.5, 0.5]]
			# func_registration.inputs.radius_or_number_of_bins = [[32, 4]]
			# func_registration.inputs.sampling_strategy = [[None, None]]
			# func_registration.inputs.sampling_percentage = [[None, None]]
			# func_registration.inputs.convergence_threshold = [-0.01]
			# func_registration.inputs.convergence_window_size = [5]
			# func_registration.inputs.smoothing_sigmas = [[1, 0.5, 0]]
			# func_registration.inputs.sigma_units = ['vox']
			# func_registration.inputs.shrink_factors = [[4, 2, 1]]
			# func_registration.inputs.use_estimate_learning_rate_once = [True]
			# func_registration.inputs.use_histogram_matching = [True]
			# func_registration.inputs.winsorize_lower_quantile = 0.005
			# func_registration.inputs.winsorize_upper_quantile = 0.995
			# func_registration.inputs.args = '--float'
			# func_registration.inputs.num_threads = 4

			func_registration.inputs.moving_image = func_BET_res.outputs.out_file
			func_registration.inputs.output_warped_image = 'f_{}_ofM{}.nii.gz'.format(participant,i)
			func_registration_res = func_registration.run()

			warp = ants.ApplyTransforms()
			warp.inputs.reference_image = template
			warp.inputs.input_image_type = 3
			warp.inputs.interpolation = 'Linear'
			warp.inputs.invert_transform_flags = [False, False]
			warp.inputs.terminal_output = 'file'
			warp.inputs.output_image = '{}_ofM{}.nii.gz'.format(participant,i)
			warp.num_threads = 4

			warp.inputs.input_image = func_image
			warp.inputs.transforms = [func_registration_res.outputs.composite_transform, struct_registration_res.outputs.composite_transform]
			warp.run()

if __name__ == '__main__':
	structural_per_participant_test("4001")
	# functional_per_participant_test()
	# structural_to_functional_per_participant_test("4009")
	# structural_to_functional_per_participant_test("4008")
	# structural_to_functional_per_participant_test("4007")
	# structural_to_functional_per_participant_test("4001")
	# canonical("4012",[""])
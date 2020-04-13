import argparse
import colour
import importlib.util
import os
import sys
import types

import manimlib.constants


def parse_cli():
    """
    Parses the user input from the terminal using the built-int argparse. 
    Returns args: a Namespace object with all the parsed commands and filenames.
    """
    try:
        parser = argparse.ArgumentParser()
        # Only one of the options in module_location can be present.
        module_location = parser.add_mutually_exclusive_group()
        # Positional argument. Stores path to file with scenes.
        # nargs="?": argument consumed if possible and produced as a single item. 
        # This is because this is not used when livestream is in use. 
        # Note that using - as filename, we can follow it up with code. 
        module_location.add_argument(
            "file",
            nargs="?",
            help="path to file holding the python code for the scene",
        )
        # Positional argument. Stores name(s) of scenes to render.
        # nargs="*": all arguments are gathered into a list. 
        parser.add_argument(
            "scene_names",
            nargs="*",
            help="Name of the Scene class you want to see",
        )
        # Optional argument flag. Stores True if present else False.
        parser.add_argument(
            "-p", "--preview",
            action="store_true",
            help="Automatically open the saved file once its done",
        ),
        parser.add_argument(
            "-w", "--write_to_movie",
            action="store_true",
            help="Render the scene as a movie file",
        ),
        parser.add_argument(
            "-s", "--save_last_frame",
            action="store_true",
            help="Save the last frame",
        ),
        parser.add_argument(
            "-l", "--low_quality",
            action="store_true",
            help="Render at a low quality (for faster rendering)",
        ),
        parser.add_argument(
            "-m", "--medium_quality",
            action="store_true",
            help="Render at a medium quality",
        ),
        parser.add_argument(
            "--high_quality",
            action="store_true",
            help="Render at a high quality",
        ),
        parser.add_argument(
            "-g", "--save_pngs",
            action="store_true",
            help="Save each frame as a png",
        ),
        parser.add_argument(
            "-i", "--save_as_gif",
            action="store_true",
            help="Save the video as gif",
        ),
        parser.add_argument(
            "-f", "--show_file_in_finder",
            action="store_true",
            help="Show the output file in finder",
        ),
        parser.add_argument(
            "-t", "--transparent",
            action="store_true",
            help="Render to a movie file with an alpha channel",
        ),
        parser.add_argument(
            "-q", "--quiet",
            action="store_true",
            help="",
        ),
        parser.add_argument(
            "-a", "--write_all",
            action="store_true",
            help="Write all the scenes from a file",
        ),
        # Argument requires a path to where to store the output.
        parser.add_argument(
            "-o", "--file_name",
            help="Specify the name of the output file, if"
                 "it should be different from the scene class name",
        )
        # Arguemnt requires input number or e.g. '3,6'.
        parser.add_argument(
            "-n", "--start_at_animation_number",
            help="Start rendering not from the first animation, but"
                 "from another, specified by its index.  If you pass"
                 "in two comma separated values, e.g. \"3,6\", it will end"
                 "the rendering at the second value",
        )
        # Argument with input. 
        parser.add_argument(
            "-r", "--resolution",
            help="Resolution, passed as \"height,width\"",
        )
        # Argument with input.
        parser.add_argument(
            "-c", "--color",
            help="Background color",
        )
        # Flag
        parser.add_argument(
            "--sound",
            action="store_true",
            help="Play a success/failure sound",
        )
        # Flag
        parser.add_argument(
            "--leave_progress_bars",
            action="store_true",
            help="Leave progress bars displayed in terminal",
        )
        # Argument with input.
        parser.add_argument(
            "--media_dir",
            help="directory to write media",
        )
        video_group = parser.add_mutually_exclusive_group()
        # Only one of the two below can be given.
        video_group.add_argument(
            "--video_dir",
            help="directory to write file tree for video",
        )
        video_group.add_argument(
            "--video_output_dir",
            help="directory to write video",
        )
        parser.add_argument(
            "--tex_dir",
            help="directory to write tex",
        )

        # For live streaming
        # Cannot include --livestream if filename is given. 
        module_location.add_argument(
            "--livestream",
            action="store_true",
            help="Run in streaming mode",
        )
        parser.add_argument(
            "--to-twitch",
            action="store_true",
            help="Stream to twitch",
        )
        parser.add_argument(
            "--with-key",
            dest="twitch_key",
            help="Stream key for twitch",
        )
        args = parser.parse_args()

        if args.file is None and not args.livestream:
            parser.print_help()
            sys.exit(2)
        if args.to_twitch and not args.livestream:
            print("You must run in streaming mode in order to stream to twitch")
            sys.exit(2)
        if args.to_twitch and args.twitch_key is None:
            print("Specify the twitch stream key with --with-key")
            sys.exit(2)
        return args
    except argparse.ArgumentError as err:
        print(str(err))
        sys.exit(2) # Exit code 2 is used for syntax error. 


def get_module(file_name):
    """
    Checks if input file is given. 
    If no input file is given, then it instead gets the input from 
    the input line. Probably for quick testing of functions.  
    Both alternatives returns a module object. 
    """
    if file_name == "-":
        # Create a module on the fly with the code 
        # with the code from the input line. 
        # Peobably for quick tests. 
        # Creates a module object to use its dictionary later. 
        # Not sure yet how this is used. I might be wrong. (???) 
        module = types.ModuleType("input_scenes") 
        code = "from manimlib.imports import *\n\n" + sys.stdin.read()
        try:
            # The code is executed.
            # The namespace of this code (e.g. where all variables are stored)
            # is module.__dict__. 
            # This means that module is used just as it were a regular 
            # module imported and from which code were ran. 
            # The module is then returned. 
            exec(code, module.__dict__)
            return module
        except Exception as e:
            print(f"Failed to render scene: {str(e)}")
            sys.exit(2)
    else:
        # Replace e.g. 'jens/input.py' with 'jens.input' 
        module_name = file_name.replace(os.sep, ".").replace(".py", "")
        # A spec is a Namespace that contains import-related information 
        # used to load a module. 
        spec = importlib.util.spec_from_file_location(module_name, file_name)
        # Create a new module based on spec and spec.loader.create_module
        module = importlib.util.module_from_spec(spec)
        # A spec object has a loader object. 
        spec.loader.exec_module(module)
        return module


def get_configuration(args):
    module = get_module(args.file)
    file_writer_config = {
        # By default, write to file
        "write_to_movie": args.write_to_movie or not args.save_last_frame,
        "save_last_frame": args.save_last_frame,
        "save_pngs": args.save_pngs,
        "save_as_gif": args.save_as_gif,
        # If -t is passed in (for transparent), this will be RGBA
        "png_mode": "RGBA" if args.transparent else "RGB",
        "movie_file_extension": ".mov" if args.transparent else ".mp4",
        "file_name": args.file_name,
        "input_file_path": args.file,
    }
    if hasattr(module, "OUTPUT_DIRECTORY"):
        file_writer_config["output_directory"] = module.OUTPUT_DIRECTORY
    config = {
        "module": module,
        "scene_names": args.scene_names,
        "open_video_upon_completion": args.preview,
        "show_file_in_finder": args.show_file_in_finder,
        "file_writer_config": file_writer_config,
        "quiet": args.quiet or args.write_all,
        "ignore_waits": args.preview,
        "write_all": args.write_all,
        "start_at_animation_number": args.start_at_animation_number,
        "end_at_animation_number": None,
        "sound": args.sound,
        "leave_progress_bars": args.leave_progress_bars,
        "media_dir": args.media_dir,
        "video_dir": args.video_dir,
        "video_output_dir": args.video_output_dir,
        "tex_dir": args.tex_dir,
    }

    # Camera configuration
    config["camera_config"] = get_camera_configuration(args)

    # Arguments related to skipping
    stan = config["start_at_animation_number"]
    if stan is not None:
        if "," in stan:
            start, end = stan.split(",")
            config["start_at_animation_number"] = int(start)
            config["end_at_animation_number"] = int(end)
        else:
            config["start_at_animation_number"] = int(stan)

    config["skip_animations"] = any([
        file_writer_config["save_last_frame"],
        config["start_at_animation_number"],
    ])
    return config


def get_camera_configuration(args):
    camera_config = {}
    if args.low_quality:
        camera_config.update(manimlib.constants.LOW_QUALITY_CAMERA_CONFIG)
    elif args.medium_quality:
        camera_config.update(manimlib.constants.MEDIUM_QUALITY_CAMERA_CONFIG)
    elif args.high_quality:
        camera_config.update(manimlib.constants.HIGH_QUALITY_CAMERA_CONFIG)
    else:
        camera_config.update(manimlib.constants.PRODUCTION_QUALITY_CAMERA_CONFIG)

    # If the resolution was passed in via -r
    if args.resolution:
        if "," in args.resolution:
            height_str, width_str = args.resolution.split(",")
            height = int(height_str)
            width = int(width_str)
        else:
            height = int(args.resolution)
            width = int(16 * height / 9)
        camera_config.update({
            "pixel_height": height,
            "pixel_width": width,
        })

    if args.color:
        try:
            camera_config["background_color"] = colour.Color(args.color)
        except AttributeError as err:
            print("Please use a valid color")
            print(err)
            sys.exit(2)

    # If rendering a transparent image/move, make sure the
    # scene has a background opacity of 0
    if args.transparent:
        camera_config["background_opacity"] = 0

    return camera_config

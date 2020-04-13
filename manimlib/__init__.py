#!/usr/bin/env python
"""
Parses the terminal input and stores in args. 
Converts args to correct format and store in config. 
Initialize the folders needed. 
Extract the scenes. 
The name of the scene names are passed in via the config variable, and ultimately
via the command line command that was parsed. 
If args.livestream is set, then it instead starts the live stream to Twitch.
"""
import manimlib.config
import manimlib.constants
import manimlib.extract_scene
import manimlib.stream_starter


def main():
    args = manimlib.config.parse_cli()
    if not args.livestream:
        config = manimlib.config.get_configuration(args)
        manimlib.constants.initialize_directories(config)
        manimlib.extract_scene.main(config)
    else:
        manimlib.stream_starter.start_livestream(
            to_twitch=args.to_twitch,
            twitch_key=args.twitch_key,
        )

#!/usr/bin/env python

"Checks if you are running livestreaming. If not it runs the proper main file in manimlib. "
import manimlib

if __name__ == "__main__":
    manimlib.main()
else:
    manimlib.stream_starter.start_livestream()

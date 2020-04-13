#!/usr/bin/env python

"""
Checks if you are running livestreaming. 
If not it runs the main() from the manimlib.__init__.py file. 
"""
import manimlib

if __name__ == "__main__":
    manimlib.main()
else:
    manimlib.stream_starter.start_livestream()

"""
Register FnKivy-ui widgets to use without import.
"""

from kivy.factory import Factory

def register():
    register = Factory.register

    # ---) Base Widget
    register("Scene", module="kivyfn.three.scene")

# -*- coding: utf-8 -*-
def classFactory(iface):
    from .vl_locator_plugin import VisibleLayersLocatorPlugin
    return VisibleLayersLocatorPlugin(iface)

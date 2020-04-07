import tango
from bluesky import RunEngine
from bluesky.callbacks.core import LiveTable
from bluesky.plans import count
from ophyd import Component as Cpt
from ophyd import Device


class TangoAttribute:
    "Wrap a tango.AttributeProxy in the bluesky interface."

    def __init__(self, tango_name, *args, parent=None, **kwargs):
        self.kind = kwargs.get("kind", 1)
        self.attr_name = kwargs.get("attr_name", "")
        self._attribute_proxy = tango.AttributeProxy(tango_name)
        self.name = self._attribute_proxy.name()
        self.parent = parent

    def read(self):
        reading = self._attribute_proxy.read()
        return {
            self.name: {
                "value": reading.value,
                "timestamp": reading.time.totime(),
            }
        }

    def describe(self):
        return {
            self.name: {
                "shape": extract_shape(self._attribute_proxy.read()),
                "dtype": "number",  # jsonschema types
                "source": "...",
                "unit": "...",
            }
        }

    def read_configuration(self):
        return {}

    def describe_configuration(self):
        return {}


class TangoDevice:
    "Wrap a tango.DeviceProxy in the bluesky interface."

    def __init__(self, device_name, read_attrs=None, *, parent=None):
        self.read_attrs = read_attrs
        self.proxy = tango.DeviceProxy(device_name)
        self.attrs = self.proxy.get_attribute_list()
        self.name = self.proxy.dev_name().replace("/", ":")
        self.parent = parent

    def read(self):
        if self.read_attrs is None:
            read_attrs = self.attrs
        else:
            read_attrs = self.read_attrs
        data = {
            attr.name: {"value": attr.value, "timestamp": attr.time.totime()}
            for attr in self.proxy.read_attributes(read_attrs)
        }
        return data

    def describe(self):
        return {
            attr.name: {
                "shape": extract_shape_from_config(attr),
                "dtype": "number",  # jsonschema types
                "source": "...",
                "unit": "...",
            }
            for attr in self.proxy.attribute_list_query()
        }

    def read_configuration(self):
        return {}

    def describe_configuration(self):
        return {}


def extract_shape_from_config(config):
    shape = []  # e.g. [10, 15]
    if config.max_dim_x:
        shape.append(config.max_dim_x)
    if config.max_dim_y:
        shape.append(config.max_dim_y)
    return shape


def extract_shape(reading):
    shape = []  # e.g. [10, 15]
    if reading.dim_x:
        shape.append(reading.dim_x)
    if reading.dim_y:
        shape.append(reading.dim_y)
    return shape


class DeviceAttrNames(Device):
    dou = Cpt(TangoAttribute, "/double_scalar")
    flo = Cpt(TangoAttribute, "/float_scalar")


class DeviceFullNames(Device):
    dou = Cpt(TangoAttribute, "sys/tg_test/1/double_scalar")
    flo = Cpt(TangoAttribute, "sys/tg_test/1/float_scalar")


tango_attr = TangoAttribute("sys/tg_test/1/double_scalar")
device_attr_names = DeviceAttrNames("sys/tg_test/1", name="some_name")
device_full_names = DeviceFullNames("", name="another_name")
device_tango = TangoDevice("sys/tg_test/1", ["ampli", "double_scalar"])

RE = RunEngine()

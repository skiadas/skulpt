import random

try:
    from vega_caller import render_graph
except:
    print("Mock render")

    def render_graph(js):
        print(js)


class Chart:
    # TODO allow data to be specified as a URL to a CSV or DB or json
    def __init__(self, data, title=None):
        self.title = title
        self.data_id = random.randrange(1000000, 5000000)
        self.dsname = "data-{}".format(self.data_id)
        if isinstance(data, dict):
            self.data = Data(**data)
        else:
            self.data = data

        self.json = {}
        self.json["$schema"] = "https://vega.github.io/schema/vega-lite/v2.5.json"
        self.json["data"] = {}
        if self.title:
            self.json["title"] = self.title

        self.json["data"] = {"values": self.data.vals}
        self.is_composite = False

    # mark can be a simple string or a dictionary
    # "mark": {"color": "green", "opacity": 0.2, "type": "rect"}

    def mark_json(self, mark_type, **kwargs):
        if kwargs:
            self.json["mark"] = {}
            self.json["mark"]["type"] = mark_type
            self.json["mark"].update(kwargs)
        else:
            self.json["mark"] = mark_type

        return self

    def mark_bar(self, **kwargs):
        return self.mark_json("bar", **kwargs)

    def mark_point(self, **kwargs):
        return self.mark_json("point", **kwargs)

    def mark_line(self, **kwargs):
        return self.mark_json("line", **kwargs)

    def mark_rect(self, **kwargs):
        return self.mark_json("rect", **kwargs)

    def mark_area(self, **kwargs):
        return self.mark_json("area", **kwargs)

    def mark_tick(self, **kwargs):
        return self.mark_json("tick", **kwargs)

    def encode(self, x="", y="", color="", size="", tooltip=""):
        self.encoding = {}
        if x:
            if isinstance(x, Axis):
                self.encoding["x"] = x.toJson()
            else:
                self.encoding["x"] = Axis(x).toJson()
        if y:
            if isinstance(y, Axis):
                self.encoding["y"] = y.toJson()
            else:
                self.encoding["y"] = Axis(y).toJson()

        # "color": {"type": "nominal", "field": "species"}
        if color:
            field, tp = _get_name_type(color)
            self.encoding["color"] = dict(type=tp, field=field)

        # "size": {"type": "quantitative", "field": "Acceleration"}
        if size:
            field, tp = _get_name_type(size)
            self.encoding["size"] = dict(type=tp, field=field)

        if tooltip:
            field, tp = _get_name_type(tooltip)
            self.encoding["tooltip"] = dict(type=tp, field=field)

        self.json["encoding"] = self.encoding
        return self

    def interactive(self):
        iconfig = {
            "selector002": {
                "type": "interval",
                "bind": "scales",
                "encodings": ["x", "y"],
                "on": "[mousedown, window:mouseup] > window:mousemove!",
                "translate": "[mousedown, window:mouseup] > window:mousemove!",
                "zoom": "wheel!",
                "mark": {"fill": "#333", "fillOpacity": 0.125, "stroke": "white"},
                "resolve": "global",
            }
        }
        self.json["selection"] = iconfig
        return self

    def display(self):
        render_graph(self.json)

    def __add__(self, other):
        return self.add_layer(other, "layer")

    def __and__(self, other):
        return self.add_layer(other, "vconcat")

    def __or__(self, other):
        return self.add_layer(other, "hconcat")

    def add_layer(self, other, lname):
        # multle layers are added by concatenating the new element to the
        # existing layer.  If the layer does not exist then initialize
        # it from self.
        if lname not in self.json:
            self.json[lname] = []
            self.json["datasets"] = {}
            temp = {}
            temp["data"] = {"name": self.dsname}
            self.json["datasets"][self.dsname] = self.json["data"]["values"]
            del self.json["data"]
            temp["encoding"] = self.json["encoding"]
            del self.json["encoding"]
            temp["mark"] = self.json["mark"]
            del self.json["mark"]
            self.json[lname].append(temp)
        temp = {}
        self.json["datasets"][other.dsname] = other.json["data"]["values"]
        temp["data"] = {"name": other.dsname}
        temp["encoding"] = other.json["encoding"]
        temp["mark"] = other.json["mark"]
        self.json[lname].append(temp)
        return self


#   "datasets": {
#     "data-e56e43354d9b8f2ab0d1e90cf27cd47f": [
#       {"a": 4, "b": 1, "c": "r"},
#       {"a": 5, "b": 2, "c": "g"},
#       {"a": 6, "b": 3, "c": "b"}
#     ],
#     "data-a4c3047a15bf9380c2e615cf87648369": [
#       {"a": 1, "b": 4, "c": "r"},
#       {"a": 2, "b": 5, "c": "g"},
#       {"a": 3, "b": 6, "c": "b"}
#     ]
#   }

# TODO:  add a rect mark type for a heat map


def _get_name_type(name):
    typed = {"Q": "quantitative", "O": "ordinal", "N": "nominal", "T": "temporal"}
    nt = name.split(":")
    tstring = "quantitative"
    if len(nt) == 2:
        tstring = typed[nt[1]]
    return nt[0], tstring


class Axis:
    def __init__(self, name, bin=False):
        self.aggregate = None
        self.name, self.type = _get_name_type(name)
        if "()" in self.name:  # aggregate function
            self.aggregate = self.name.replace("()", "")
            self.name = None
        self.bin = bin

    def toJson(self):
        json = {}
        if self.name:
            json["field"] = self.name
        if self.type:
            json["type"] = self.type
        if self.bin:
            json["bin"] = True
        if self.aggregate:
            json["aggregate"] = self.aggregate

        return json


class X(Axis):
    pass


class Y(Axis):
    pass


class Data:
    def __init__(self, **kwargs):
        """
        input can be the form of a series of keyword args where
        the keyword is the column name, or a single keyword data
        that is a list of json style records as rows.
        could also accept a csv file? or keywords columns and rows
        This accepts a lot more options that "real altair" to make it easier
        to work with non-DataFrame data sets.  Internally:
        self.keys contains the list of column names
        self.vals is a list of dictionaries of the form [{col1:val1, col2:val2, ... coln:valn},
                                                         {col1:val3, col2:val4, ... coln:valn},
                                                         {col1:val5, col2:val6, ... coln:valn}]
        """
        # todo: accept a URL as the argument to read a CSV or JSON file
        if len(kwargs) == 1 and "data" in kwargs:
            self.data = kwargs["data"]
            self.keys = self.data[0].keys()
            self.vals = self.data
        elif len(kwargs) == 2 and ("columns" in kwargs) and ("rows" in kwargs):
            self.keys = kwargs["columns"]
            self.vals = []
            for r in kwargs["rows"]:
                self.vals.append(dict(zip(self.keys, r)))
        else:
            keys = kwargs.keys()
            vals = []
            primary_key = list(keys)[0]
            for ix in range(len(kwargs[primary_key])):
                d = {}
                for key in keys:
                    d[key] = kwargs[key][ix]
                vals.append(d)
            self.vals = vals
            self.keys = keys

    def __str__(self):
        # header = "\t".join(self.keys) + "\n"
        header = ""
        for key in self.keys:
            header += key.center(10) + " "
        header += "\n"
        template = ""
        for key in self.keys:
            template += "{" + key + ": <10} "
        template += "\n"
        res = ""
        for row in self.vals:
            res += template.format(**row)

        return header + res


if __name__ == "__main__":
    d = Data(a=[3, 4, 5], b=[1, 2, 3], c=["r", "g", "b"])
    print(d)
    print(
        type(
            Chart({"a": list("abc"), "b": [1, 2, 3]}).mark_bar().encode(x="a:N", y="b")
        )
    )
    aa = (
        Chart(Data(a=[3, 4, 5], b=[1, 2, 3], c=["r", "g", "b"]))
        .mark_point(color="red")
        .encode(x="b", y="a", color="c:O")
    )
    print("aa = ", aa)
    aa.display()

    bb = (
        Chart(Data(a=[1, 2, 3], b=[4, 5, 6], c=["r", "g", "b"]))
        .mark_line()
        .encode(x="b", y="a", color="c:O")
    )
    print("bb = ", bb)
    bb.display()
    print("aa+bb", (aa + bb).display())
    # Chart(Data(a=[1,2,3,2,2,4,5,5,6,7,8,8,8,8,8,9,0,0])).mark_bar().encode(Axis('a:Q', bin=True),y='count()')


# todo: see if I can work with the repr of an object to get the behavior that altair gets in notebooks
# todo: implement a Bin object to specifiy maxbins

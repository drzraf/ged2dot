#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

"""A version of ged2dot that uses breadth-first search to traverse the gedcom graph."""

from typing import BinaryIO
from typing import Dict
from typing import List
from typing import Optional
from typing import cast
import argparse
import configparser
import os
import sys


class Config:
    """Stores options from a config file or from cmdline args."""
    def __init__(self) -> None:
        self.input = "-"
        self.output = "-"
        self.rootfamily = "F1"
        # Could be 0, but defaulting to something that can easily explode on large input is not
        # helpful.
        self.familydepth = "3"
        self.imagedir = "images"
        self.nameorder = "little"

    def read_config(self, config_file: str) -> None:
        """Reads config from a provided file."""
        if not config_file:
            return
        config_parser = configparser.ConfigParser()
        config_parser.read(config_file)
        for section in config_parser.sections():
            if section != "ged2dot":
                continue
            for option in config_parser.options(section):
                self.__setattr__(option, config_parser.get(section, option))

    def read_args(self, args: argparse.Namespace) -> None:
        """Reads config from cmdline args."""
        if args.input:
            self.input = args.input
        if args.output:
            self.output = args.output
        if args.rootfamily:
            self.rootfamily = args.rootfamily
        if args.familydepth:
            self.familydepth = args.familydepth
        if args.imagedir:
            self.imagedir = args.imagedir
        if args.nameorder:
            self.nameorder = args.nameorder

    def get_dict(self) -> Dict[str, str]:
        """Gets the config as a dict."""
        config = {
            "input": self.input,
            "output": self.output,
            "rootfamily": self.rootfamily,
            "familydepth": self.familydepth,
            "imagedir": self.imagedir,
            "nameorder": self.nameorder,
        }
        return config


class Node:
    """Base class for an individual or family."""
    def get_identifier(self) -> str:  # pragma: no cover
        """Gets the ID of this node."""
        # pylint: disable=no-self-use
        ...

    def set_depth(self, depth: int) -> None:  # pragma: no cover
        """Set the depth of this node, during one graph traversal."""
        # pylint: disable=no-self-use
        # pylint: disable=unused-argument
        ...

    def get_depth(self) -> int:  # pragma: no cover
        """Get the depth of this node, during one graph traversal."""
        # pylint: disable=no-self-use
        ...

    def get_neighbours(self) -> List["Node"]:  # pragma: no cover
        """Get the neighbour nodes of this node."""
        # pylint: disable=no-self-use
        ...

    def resolve(self, graph: List["Node"]) -> None:  # pragma: no cover
        """Resolve string IDs to node objects."""
        # pylint: disable=no-self-use
        # pylint: disable=unused-argument
        ...


def graph_find(graph: List[Node], identifier: str) -> Optional[Node]:
    """Find identifier in graph."""
    if not identifier:
        return None

    results = [node for node in graph if node.get_identifier() == identifier]
    assert len(results) == 1
    return results[0]


def get_abspath(path: str) -> str:
    """Make a path absolute, taking the repo root as a base dir."""
    if os.path.isabs(path):
        return path

    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def get_data_abspath(gedcom: str, path: str) -> str:
    """Make a path absolute, taking the gedcom file's dir as a base dir."""
    if os.path.isabs(path):
        return path

    return os.path.join(os.path.dirname(os.path.realpath(gedcom)), path)


def to_bytes(string: str) -> bytes:
    """Encodes the string to UTF-8."""
    return string.encode("utf-8")


class IndividualConfig:
    """Key-value pairs on an individual."""
    def __init__(self) -> None:
        self.__note = ""
        self.__birth = ""
        self.__death = ""

    def set_note(self, note: str) -> None:
        """Sets a note."""
        self.__note = note

    def get_note(self) -> str:
        """Gets a note."""
        return self.__note

    def set_birth(self, birth: str) -> None:
        """Sets the birth date."""
        self.__birth = birth

    def get_birth(self) -> str:
        """Gets the birth date."""
        return self.__birth

    def set_death(self, death: str) -> None:
        """Sets the death date."""
        self.__death = death

    def get_death(self) -> str:
        """Gets the death date."""
        return self.__death


class Individual(Node):
    """An individual is always a child in a family, and is an adult in 0..* families."""
    def __init__(self) -> None:
        self.__dict: Dict[str, str] = {}
        self.__dict["identifier"] = ""
        self.__dict["famc_id"] = ""
        self.famc: Optional[Family] = None
        self.fams_ids: List[str] = []
        self.fams_list: List["Family"] = []
        self.depth = 0
        self.__dict["forename"] = ""
        self.__dict["surname"] = ""
        self.__dict["sex"] = ""
        self.__config = IndividualConfig()

    def __str__(self) -> str:
        # Intentionally only print the famc/fams IDs, not the whole object to avoid not wanted
        # recursion.
        ret = "Individual(__dict=" + str(self.__dict)
        ret += ", fams_ids: " + str(self.fams_ids)
        ret += ", depth: " + str(self.depth) + ")"
        return ret

    def resolve(self, graph: List[Node]) -> None:
        self.famc = cast(Optional["Family"], graph_find(graph, self.get_famc_id()))
        for fams_id in self.fams_ids:
            fams = graph_find(graph, fams_id)
            assert fams
            self.fams_list.append(cast("Family", fams))

    def get_neighbours(self) -> List[Node]:
        ret: List[Node] = []
        if self.famc:
            ret.append(self.famc)
        ret += self.fams_list
        return ret

    def get_config(self) -> IndividualConfig:
        """Returns key-value pairs of individual."""
        return self.__config

    def set_identifier(self, identifier: str) -> None:
        """Sets the ID of this individual."""
        self.__dict["identifier"] = identifier

    def get_identifier(self) -> str:
        return self.__dict["identifier"]

    def set_sex(self, sex: str) -> None:
        """Sets the sex of this individual."""
        self.__dict["sex"] = sex

    def get_sex(self) -> str:
        """Gets the sex of this individual."""
        return self.__dict["sex"]

    def set_forename(self, forename: str) -> None:
        """Sets the first name of this individual."""
        self.__dict["forename"] = forename

    def get_forename(self) -> str:
        """Gets the first name of this individual."""
        return self.__dict["forename"]

    def set_surname(self, surname: str) -> None:
        """Sets the family name of this individual."""
        self.__dict["surname"] = surname

    def get_surname(self) -> str:
        """Gets the family name of this individual."""
        return self.__dict["surname"]

    def set_depth(self, depth: int) -> None:
        self.depth = depth

    def get_depth(self) -> int:
        return self.depth

    def set_famc_id(self, famc_id: str) -> None:
        """Sets the child family ID."""
        self.__dict["famc_id"] = famc_id

    def get_famc_id(self) -> str:
        """Gets the child family ID."""
        return self.__dict["famc_id"]

    def get_label(self, image_dir: str, name_order: str) -> str:
        """Gets the graphviz label."""
        image_path = os.path.join(image_dir, self.get_forename() + " " + self.get_surname())
        image_path += " " + self.get_config().get_birth() + ".jpg"
        if not os.path.exists(to_bytes(image_path)):
            if self.get_sex():
                sex = self.get_sex().lower()
            else:
                sex = 'u'
            image_path = get_abspath("placeholder-%s.png" % sex)
        label = "<table border=\"0\" cellborder=\"0\"><tr><td>"
        label += "<img src=\"" + image_path + "\"/>"
        label += "</td></tr><tr><td>"
        if name_order == "big":
            # Big endian: family name first.
            label += self.get_surname() + "<br/>"
            label += self.get_forename() + "<br/>"
        else:
            # Little endian: given name first.
            label += self.get_forename() + "<br/>"
            label += self.get_surname() + "<br/>"
        label += self.get_config().get_birth() + "-" + self.get_config().get_death()
        label += "</td></tr></table>"
        return label

    def get_color(self) -> str:
        """Gets the color around the node."""
        if not self.get_sex():
            sex = 'U'
        else:
            sex = self.get_sex().upper()
        color = {'M': 'blue', 'F': 'pink', 'U': 'black'}[sex]
        return color


class Family(Node):
    """Family has exactly one wife and husband, 0..* children."""
    def __init__(self) -> None:
        self.__dict: Dict[str, str] = {}
        self.__dict["identifier"] = ""
        self.__dict["wife_id"] = ""
        self.wife: Optional["Individual"] = None
        self.__dict["husb_id"] = ""
        self.husb: Optional["Individual"] = None
        self.child_ids: List[str] = []
        self.child_list: List["Individual"] = []
        self.depth = 0

    def __str__(self) -> str:
        # Intentionally only print the wife/husband/child IDs, not the whole object to avoid not
        # wanted recursion.
        ret = "Family(__dict=" + str(self.__dict)
        ret += ", child_ids: " + str(self.child_ids)
        ret += ", depth: " + str(self.depth) + ")"
        return ret

    def resolve(self, graph: List[Node]) -> None:
        self.wife = cast(Optional["Individual"], graph_find(graph, self.get_wife_id()))
        self.husb = cast(Optional["Individual"], graph_find(graph, self.get_husb_id()))
        for child_id in self.child_ids:
            child = graph_find(graph, child_id)
            assert child
            self.child_list.append(cast("Individual", child))

    def get_neighbours(self) -> List[Node]:
        ret: List[Node] = []
        if self.wife:
            ret.append(self.wife)
        if self.husb:
            ret.append(self.husb)
        ret += self.child_list
        return ret

    def set_identifier(self, identifier: str) -> None:
        """Sets the ID of this family."""
        self.__dict["identifier"] = identifier

    def get_identifier(self) -> str:
        return self.__dict["identifier"]

    def set_depth(self, depth: int) -> None:
        self.depth = depth

    def get_depth(self) -> int:
        return self.depth

    def set_wife_id(self, wife_id: str) -> None:
        """Sets the wife ID of this family."""
        self.__dict["wife_id"] = wife_id

    def get_wife_id(self) -> str:
        """Gets the wife ID of this family."""
        return self.__dict["wife_id"]

    def set_husb_id(self, husb_id: str) -> None:
        """Sets the husband ID of this family."""
        self.__dict["husb_id"] = husb_id

    def get_husb_id(self) -> str:
        """Gets the husband ID of this family."""
        return self.__dict["husb_id"]


class GedcomImport:
    """Builds the graph from GEDCOM."""
    def __init__(self) -> None:
        self.individual: Optional[Individual] = None
        self.family: Optional[Family] = None
        self.graph: List[Node] = []
        self.in_birt = False
        self.in_deat = False

    def __reset_flags(self) -> None:
        if self.in_birt:
            self.in_birt = False
        elif self.in_deat:
            self.in_deat = False

    def __handle_level0(self, line: str) -> None:
        if self.individual:
            self.graph.append(self.individual)
            self.individual = None
        if self.family:
            self.graph.append(self.family)
            self.family = None

        if line.startswith("@") and line.endswith("INDI"):
            self.individual = Individual()
            self.individual.set_identifier(line[1:-6])
        elif line.startswith("@") and line.endswith("FAM"):
            self.family = Family()
            self.family.set_identifier(line[1:-5])

    def __handle_level1(self, line: str) -> None:
        self.__reset_flags()

        line_lead_token = line.split(' ')[0]

        if line_lead_token == "SEX" and self.individual:
            tokens = line.split(' ')
            if len(tokens) > 1:
                self.individual.set_sex(tokens[1])
        elif line_lead_token == "NAME" and self.individual:
            line = line[5:]
            tokens = line.split('/')
            self.individual.set_forename(tokens[0].strip())
            if len(tokens) > 1:
                self.individual.set_surname(tokens[1].strip())
        elif line_lead_token == "FAMC" and self.individual:
            # At least <https://www.ancestry.com> sometimes writes multiple FAMC, which doesn't
            # make sense. Import only the first one.
            if not self.individual.get_famc_id():
                self.individual.set_famc_id(line[6:-1])
        elif line_lead_token == "FAMS" and self.individual:
            self.individual.fams_ids.append(line[6:-1])
        elif line_lead_token == "HUSB" and self.family:
            self.family.set_husb_id(line[6:-1])
        elif line_lead_token == "WIFE" and self.family:
            self.family.set_wife_id(line[6:-1])
        elif line_lead_token == "CHIL" and self.family:
            self.family.child_ids.append(line[6:-1])
        else:
            self.__handle_individual_config(line)

    def __handle_individual_config(self, line: str) -> None:
        """Handles fields stored in individual.get_config()."""
        line_lead_token = line.split(' ')[0]

        if line_lead_token == "BIRT":
            self.in_birt = True
        elif line_lead_token == "DEAT":
            self.in_deat = True
        elif line_lead_token == "NOTE" and self.individual:
            self.individual.get_config().set_note(line[5:])

    def load(self, config: Dict[str, str]) -> List[Node]:
        """Tokenizes and resolves a gedcom file into a graph."""
        graph = self.tokenize(config)
        for node in graph:
            node.resolve(graph)
        return graph

    def tokenize(self, config: Dict[str, str]) -> List[Node]:
        """Tokenizes a gedcom file into a graph."""
        if config["input"] == "-":
            return self.tokenize_from_stream(sys.stdin.buffer)
        with open(config["input"], "rb") as stream:
            return self.tokenize_from_stream(stream)

    def tokenize_from_stream(self, stream: BinaryIO) -> List[Node]:
        """Tokenizes a gedcom steam into a graph."""
        for line_bytes in stream.read().split(b"\r\n"):
            line = line_bytes.strip().decode("utf-8")
            if not line:
                continue
            tokens = line.split(" ")

            first_token = tokens[0]
            # Ignore UTF-8 BOM, if there is one at the begining of the line.
            if first_token.startswith("\ufeff"):
                first_token = first_token[1:]

            level = int(first_token)
            rest = " ".join(tokens[1:])
            if level == 0:
                self.__handle_level0(rest)
            elif level == 1:
                self.__handle_level1(rest)
            elif level == 2:
                if rest.startswith("DATE") and self.individual:
                    year = rest.split(' ')[-1]
                    if self.in_birt:
                        self.individual.get_config().set_birth(year)
                    elif self.in_deat:
                        self.individual.get_config().set_death(year)
        return self.graph


def bfs(root: Node, config: Dict[str, str]) -> List[Node]:
    """
    Does a breadth first search traversal of the graph, from root. Returns the traversed nodes.
    """
    visited = [root]
    queue = [root]
    ret: List[Node] = []

    while queue:
        node = queue.pop(0)
        # Every 2nd node is a family + the root is always a family.
        family_depth = int(config["familydepth"])
        if node.get_depth() > family_depth * 2 + 1:
            return ret
        ret.append(node)
        for neighbour in node.get_neighbours():
            if neighbour not in visited:
                neighbour.set_depth(node.get_depth() + 1)
                visited.append(neighbour)
                queue.append(neighbour)

    return ret


class DotExport:
    """Serializes the graph to Graphviz / dot."""
    def __init__(self) -> None:
        self.subgraph: List[Node] = []
        self.config: Dict[str, str] = {}

    def __store_individual_nodes(self, stream: BinaryIO) -> None:
        for node in self.subgraph:
            if not isinstance(node, Individual):
                continue
            individual = node
            stream.write(to_bytes(node.get_identifier() + " [shape=box, "))
            image_dir = self.config.get("imagedir", "")
            image_dir_abs = get_data_abspath(self.config.get("input", ""), image_dir)
            name_order = self.config.get("nameorder", "little")
            stream.write(to_bytes("label = <" + individual.get_label(image_dir_abs, name_order) + ">\n"))
            stream.write(to_bytes("color = " + individual.get_color() + "];\n"))

    def __store_family_nodes(self, stream: BinaryIO) -> None:
        stream.write(to_bytes("\n"))
        for node in self.subgraph:
            if not isinstance(node, Family):
                continue
            stream.write(to_bytes(node.get_identifier() + " [shape=point, width=0.1];\n"))
        stream.write(to_bytes("\n"))

    def __store_edges(self, stream: BinaryIO) -> None:
        for node in self.subgraph:
            if not isinstance(node, Family):
                continue
            family = node
            if family.wife:
                from_wife = family.wife.get_identifier() + " -> " + family.get_identifier() + " [dir=none];\n"
                stream.write(to_bytes(from_wife))
            if family.husb:
                from_husb = family.husb.get_identifier() + " -> " + family.get_identifier() + " [dir=none];\n"
                stream.write(to_bytes(from_husb))
            for child in family.child_list:
                stream.write(to_bytes(family.get_identifier() + " -> " + child.get_identifier() + " [dir=none];\n"))

    def store(self, subgraph: List[Node], config: Dict[str, str]) -> None:
        """Exports subgraph to a graphviz path."""
        if config["output"] == "-":
            self.store_to_stream(subgraph, sys.stdout.buffer, config)
            return
        with open(config["output"], "wb") as stream:
            self.store_to_stream(subgraph, stream, config)

    def store_to_stream(self, subgraph: List[Node], stream: BinaryIO, config: Dict[str, str]) -> None:
        """Exports subgraph to a graphviz stream."""
        stream.write(to_bytes("// Generated by <https://github.com/vmiklos/ged2dot>.\n"))
        stream.write(to_bytes("digraph\n"))
        stream.write(to_bytes("{\n"))
        stream.write(to_bytes("splines = ortho;\n"))
        stream.write(to_bytes("\n"))

        self.subgraph = subgraph
        self.config = config
        self.__store_individual_nodes(stream)
        self.__store_family_nodes(stream)
        self.__store_edges(stream)

        stream.write(to_bytes("}\n"))


def convert(config: Dict[str, str]) -> None:
    """API interface."""
    importer = GedcomImport()
    graph = importer.load(config)
    root_family = graph_find(graph, config["rootfamily"])
    assert root_family
    subgraph = bfs(root_family, config)
    exporter = DotExport()
    exporter.store(subgraph, config)


def main() -> None:
    """Commandline interface."""

    # Parse config from file and cmdline args.
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str,
                        help="configuration file")
    parser.add_argument("--input", type=str,
                        help="input GEDCOM file")
    parser.add_argument("--output", type=str,
                        help="output DOT file")
    parser.add_argument("--rootfamily", type=str,
                        help="root family")
    parser.add_argument("--familydepth", type=str,
                        help="family depth")
    parser.add_argument("--imagedir", type=str,
                        help="image directory")
    parser.add_argument("--nameorder", choices=["little", "big"],
                        help="name order")
    args = parser.parse_args()
    config = Config()
    config.read_config(args.config)
    config.read_args(args)
    convert(config.get_dict())


if __name__ == '__main__':
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:

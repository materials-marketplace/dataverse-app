"""Module dedicated to the conversion of a Dataverse dataset JSON to DCAT."""

import functools
import itertools
import re
from html.parser import HTMLParser
from typing import Any, Hashable, Union

import pycountry
from jsonpath_ng.ext import parse
from rdflib import (
    DCAT,
    DCTERMS,
    FOAF,
    OWL,
    RDF,
    XSD,
    BNode,
    Graph,
    Literal,
    Namespace,
    URIRef,
)
from rdflib.term import Identifier

# from typing import Optional


# TODO: consider validating at some point the created DCAT with PySHACL.

# Custom type hints.
Triple = [Identifier, Identifier, Identifier]
# Pattern = tuple[Optional[Identifier], Optional[Identifier],
#                 Optional[Identifier]]
JSON = Any  # Placeholder for JSON type hint.

# Additional namespaces.
PAV = Namespace("http://pav-ontology.github.io/pav/")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")

# RFC3987 regex (to match IRIs) (MIT Licensed)
#  https://github.com/aas-core-works/abnf-to-regexp/blob
#  /412da7ae24ec6ea20e75767e08af3b05176053f3/test_data/single-regexp/rfc3987
#  /expected.out
"""MIT License

Copyright (c) 2021 Marko Ristin, Nico Braunisch, Robert Lehmann

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
rfc3987 = (
    r"[a-zA-Z][a-zA-Z0-9+\-.]*:(//(([a-zA-Z0-9\-._~\xa0-\ud7ff\uf900"
    r"-\ufdcf\ufdf0-\uffef\u10000-\u1fffd\u20000-\u2fffd\u30000"
    r"-\u3fffd\u40000-\u4fffd\u50000-\u5fffd\u60000-\u6fffd\u70000"
    r"-\u7fffd\u80000-\u8fffd\u90000-\u9fffd\ua0000-\uafffd\ub0000"
    r"-\ubfffd\uc0000-\ucfffd\ud0000-\udfffd\ue1000-\uefffd]"
    r"|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=:])*@)?"
    r"(\[((([0-9A-Fa-f]{1,4}:){6,6}"
    r"([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}"
    r"|([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5]))"
    r"|::([0-9A-Fa-f]{1,4}:){5,5}([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}"
    r"|([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5]))"
    r"|([0-9A-Fa-f]{1,4})?::([0-9A-Fa-f]{1,4}:){4,4}"
    r"([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2,2}"
    r"|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]"
    r"|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5]))"
    r"|(([0-9A-Fa-f]{1,4}:)?[0-9A-Fa-f]{1,4})?::([0-9A-Fa-f]{1,4}:)"
    r"{3,3}([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}"
    r"|([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5]))"
    r"|(([0-9A-Fa-f]{1,4}:){2}[0-9A-Fa-f]{1,4})?::"
    r"([0-9A-Fa-f]{1,4}:){2,2}([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|"
    r"([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5]))"
    r"|(([0-9A-Fa-f]{1,4}:){3}[0-9A-Fa-f]{1,4})?::"
    r"[0-9A-Fa-f]{1,4}:([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}"
    r"|([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5]))"
    r"|(([0-9A-Fa-f]{1,4}:){4}[0-9A-Fa-f]{1,4})?::"
    r"([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}"
    r"|([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5]))"
    r"|(([0-9A-Fa-f]{1,4}:){5}[0-9A-Fa-f]{1,4})?::"
    r"[0-9A-Fa-f]{1,4}|(([0-9A-Fa-f]{1,4}:){6}[0-9A-Fa-f]{1,4})?::)"
    r"|[vV][0-9A-Fa-f]{1,}\.[a-zA-Z0-9\-._~!$&'()*+,;=:]{1,})\]"
    r"|([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"\.([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])"
    r"|([a-zA-Z0-9\-._~\xa0-\ud7ff\uf900-\ufdcf\ufdf0-\uffef\u10000"
    r"-\u1fffd\u20000-\u2fffd\u30000-\u3fffd\u40000-\u4fffd\u50000"
    r"-\u5fffd\u60000-\u6fffd\u70000-\u7fffd\u80000-\u8fffd\u90000"
    r"-\u9fffd\ua0000-\uafffd\ub0000-\ubfffd\uc0000-\ucfffd\ud0000"
    r"-\udfffd\ue1000-\uefffd]|%[0-9A-Fa-f][0-9A-Fa-f]"
    r"|[!$&'()*+,;=])*)(:[0-9]*)?(/([a-zA-Z0-9\-._~\xa0-\ud7ff\uf900"
    r"-\ufdcf\ufdf0-\uffef\u10000-\u1fffd\u20000-\u2fffd\u30000"
    r"-\u3fffd\u40000-\u4fffd\u50000-\u5fffd\u60000-\u6fffd\u70000"
    r"-\u7fffd\u80000-\u8fffd\u90000-\u9fffd\ua0000-\uafffd\ub0000"
    r"-\ubfffd\uc0000-\ucfffd\ud0000-\udfffd\ue1000-\uefffd]"
    r"|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=:@])*)*"
    r"|/(([a-zA-Z0-9\-._~\xa0-\ud7ff\uf900-\ufdcf\ufdf0-\uffef\u10000"
    r"-\u1fffd\u20000-\u2fffd\u30000-\u3fffd\u40000-\u4fffd\u50000"
    r"-\u5fffd\u60000-\u6fffd\u70000-\u7fffd\u80000-\u8fffd\u90000"
    r"-\u9fffd\ua0000-\uafffd\ub0000-\ubfffd\uc0000-\ucfffd\ud0000"
    r"-\udfffd\ue1000-\uefffd]|%[0-9A-Fa-f][0-9A-Fa-f]"
    r"|[!$&'()*+,;=:@]){1,}(/([a-zA-Z0-9\-._~\xa0-\ud7ff\uf900"
    r"-\ufdcf\ufdf0-\uffef\u10000-\u1fffd\u20000-\u2fffd\u30000"
    r"-\u3fffd\u40000-\u4fffd\u50000-\u5fffd\u60000-\u6fffd\u70000"
    r"-\u7fffd\u80000-\u8fffd\u90000-\u9fffd\ua0000-\uafffd\ub0000"
    r"-\ubfffd\uc0000-\ucfffd\ud0000-\udfffd\ue1000-\uefffd]"
    r"|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=:@])*)*)?"
    r"|([a-zA-Z0-9\-._~\xa0-\ud7ff\uf900-\ufdcf\ufdf0-\uffef\u10000"
    r"-\u1fffd\u20000-\u2fffd\u30000-\u3fffd\u40000-\u4fffd\u50000"
    r"-\u5fffd\u60000-\u6fffd\u70000-\u7fffd\u80000-\u8fffd\u90000"
    r"-\u9fffd\ua0000-\uafffd\ub0000-\ubfffd\uc0000-\ucfffd\ud0000"
    r"-\udfffd\ue1000-\uefffd]|%[0-9A-Fa-f][0-9A-Fa-f]"
    r"|[!$&'()*+,;=:@]){1,}(/([a-zA-Z0-9\-._~\xa0-\ud7ff\uf900"
    r"-\ufdcf\ufdf0-\uffef\u10000-\u1fffd\u20000-\u2fffd\u30000"
    r"-\u3fffd\u40000-\u4fffd\u50000-\u5fffd\u60000-\u6fffd\u70000"
    r"-\u7fffd\u80000-\u8fffd\u90000-\u9fffd\ua0000-\uafffd\ub0000"
    r"-\ubfffd\uc0000-\ucfffd\ud0000-\udfffd\ue1000-\uefffd]"
    r"|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=:@])*)*"
    r"|([a-zA-Z0-9\-._~\xa0-\ud7ff\uf900-\ufdcf\ufdf0-\uffef\u10000"
    r"-\u1fffd\u20000-\u2fffd\u30000-\u3fffd\u40000-\u4fffd\u50000"
    r"-\u5fffd\u60000-\u6fffd\u70000-\u7fffd\u80000-\u8fffd\u90000"
    r"-\u9fffd\ua0000-\uafffd\ub0000-\ubfffd\uc0000-\ucfffd\ud0000"
    r"-\udfffd\ue1000-\uefffd]|%[0-9A-Fa-f][0-9A-Fa-f]"
    r"|[!$&'()*+,;=:@]){0,0})(\?(([a-zA-Z0-9\-._~\xa0-\ud7ff\uf900"
    r"-\ufdcf\ufdf0-\uffef\u10000-\u1fffd\u20000-\u2fffd\u30000"
    r"-\u3fffd\u40000-\u4fffd\u50000-\u5fffd\u60000-\u6fffd\u70000"
    r"-\u7fffd\u80000-\u8fffd\u90000-\u9fffd\ua0000-\uafffd\ub0000"
    r"-\ubfffd\uc0000-\ucfffd\ud0000-\udfffd\ue1000-\uefffd]"
    r"|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=:@])|[\ue000-\uf8ff\uf0000"
    r"-\uffffd\u100000-\u10fffd/?])*)?"
    r"(\#(([a-zA-Z0-9\-._~\xa0-\ud7ff\uf900-\ufdcf\ufdf0-\uffef\u10000"
    r"-\u1fffd\u20000-\u2fffd\u30000-\u3fffd\u40000-\u4fffd\u50000"
    r"-\u5fffd\u60000-\u6fffd\u70000-\u7fffd\u80000-\u8fffd\u90000"
    r"-\u9fffd\ua0000-\uafffd\ub0000-\ubfffd\uc0000-\ucfffd\ud0000"
    r"-\udfffd\ue1000-\uefffd]|%[0-9A-Fa-f][0-9A-Fa-f]"
    r"|[!$&'()*+,;=:@])|[/?])*)?"
)
# Modification: do not match empty string after ':'.
rfc3987 = r"(?=[^\s]*:[^\s])" + rfc3987
rfc3987 = re.compile(rfc3987, flags=re.IGNORECASE | re.UNICODE)


# Convert HTML to text.
class HTMLText(HTMLParser):
    """Sublcass of `HTMLParser` meant to convert HTML into plain text."""

    text: str = ""

    def handle_data(self, data: str) -> None:
        """Saves the text data from the HTML.

        Overrides the method of the parent class.
        """
        self.text += data


def html_to_text(data: str) -> str:
    """Converts HTML into plain text."""
    converter = HTMLText()
    converter.feed(data)
    return converter.text


# TODO: get rid of this algorithm and use the new Python 3.9's implementation.
#  https://docs.python.org/3/library/graphlib.html#graphlib.TopologicalSorter
def topological_sort(edges: set[tuple[Hashable, Hashable]]) -> tuple[Hashable, ...]:
    """Kanh's algorithm for topological sort.

    Kahn, Arthur B. (1962), "Topological sorting of large networks",
    Communications of the ACM, 5 (11): 558–562, doi:10.1145/368996.369025,
    S2CID 16728233

    Args:
        edges: A set of directed edge pairs (the first element is the tail
            and the second the head).
    """
    # Structure the graph as a dict for fast lookup.
    graph = dict()
    for x, y in edges:
        if x not in graph:
            graph[x] = {y}
        else:
            graph[x] |= {y}
        if y not in graph:
            graph[y] = set()

    result = []
    no_incoming_edges = set(graph.keys()) - {x for s in graph.values() for x in s}
    while no_incoming_edges:
        node = no_incoming_edges.pop()
        result += [node]
        for m in set(graph[node]):
            graph[node].remove(m)
            if m not in {x for s in graph.values() for x in s}:
                no_incoming_edges.add(m)

    if {y for x in graph.values() for y in x}:
        raise ValueError(
            "The provided set of edges has cycles, therefore "
            "topological sorting is unfeasible."
        )
    return tuple(result)


def jsonpath(path: str) -> callable:
    """Factory of decorators that annotate a function with a JSON path.

    Args:
        path: The JSON path to assign to the function as an annotation. It
            is assigned to the attribute `dataset_parsing_path` of the
            function.

    Returns:
        A decorator.
    """

    def decorator(func: callable):
        # Decorating with `functools.wraps` keeps the attributes of `func`,
        #  which is essential when used in combination with the other
        #  decorators defined in this file: `requires` and `provides`.
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            return func(*args, **kwargs)

        wrapped.dataset_parsing_path = path
        return wrapped

    return decorator


def create_dependency_decorator(annotation_variable: str) -> callable:
    """Factory of factories of decorators that annotate a function.

    Args:
        annotation_variable: the attribute used to annotate the function.

    See the docstring of `factory` for more details.
    """

    def factory(*keys: str) -> callable:
        """Factory of decorators annotating a function with dependencies.

        The strings are put in a set and assigned to the attribute
        `annotation_variable`.

        Args:
            keys: the dependencies to be assigned to the attribute
            `annotation_variable`.

        Returns:
            A decorator.
        """

        def decorator(func: callable):
            # Decorating with `functools.wraps` keeps the attributes of `func`,
            #  which is essential when used in combination with any other
            #  decorators that also annotate the function.
            @functools.wraps(func)
            def wrapped(*args, **kwargs):
                return func(*args, **kwargs)

            setattr(wrapped, annotation_variable, set(keys))
            return wrapped

        return decorator

    return factory


requires = create_dependency_decorator("dataset_parsing_requires")
"""Annotates functions with labels assigned to other functions.

The annotated function is expected to run after such other functions.
"""

provides = create_dependency_decorator("dataset_parsing_provides")
"""Annotates a function with a label.

The annotated function is expected to run before other functions for which it
has been specified that the provided label is required.
"""


class Dataset:
    """Representation of a Dataverse dataset.

    Fields still missing (WARNING: DO NOT TRUST THIS LIST YET):

    - "$.id": Seems to be internal.
    - "$.identifier": Seems to be internal. It also already on the
        persistent URL.
    - "$.protocol": Any feasible mapping in DCAT? It is also on the
        persistent URL.
    - "$.authority": It is already on the persistent URL.
    - "$.storageIdentifier": Seems to be internal.
    - "$.latestVersion.id": Seems to be internal.
    - "$.latestVersion.datasetId": Seems to be internal.
    - "$.latestVersion.datasetPersistendId": Seems to be internal.
    - "$.latestVersion.storageIdentifier": Seems to be internal.
    - "$.latestVersion.versionState": Any feasible mapping?
    - "$.latestVersion.releaseTime": Any feasible mapping?
    - "$.latestVersion.createTime": Any feasible mapping?
    - "$.fileAccessRequest"
    - "$.latestVersion.metadataBlocks.citation.fields
            [?(@.typeName == "subtitle")]"
    - "$.latestVersion.metadataBlocks.citation.fields
            [?(@.typeName == "alternativeURL")]"
    - "$.latestVersion.metadataBlocks.citation.fields
            [?(@.typeName == "otherId")]"
    - "$.latestVersion.metadataBlocks.citation.fields
            [?(@.typeName == "otherIdAgency")]"
    - "$.latestVersion.metadataBlocks.citation.fields
            [?(@.typeName == "otherIdValue")]"
    - "$.latestVersion.metadataBlocks.citation.fields
            [?(@.typeName == "otherId")]"

    Fields that require additional work (WARNING: DO NOT TRUST THIS LIST YET):
    - "$.latestVersion.termsOfUse": Contains HTML code, should be converted
        to a URI whenever possible. If no URI is available, should it
        contain just text?
    - "$.latestVersion.metadataBlocks.citation.fields
            [?(@.typeName == "author")]":
        implementation for authorIdentifierScheme and authorIdentifier missing.
    """

    doc: JSON
    identifiers: dict

    def __init__(self, doc: JSON) -> None:
        """Initialize the Dataset object.

        The object is described by its JSON representation received from the
        API call. See `examples/dataset.json` for an example of the
        structure of such an object.

        Args:
            doc: JSON object describing the Dataset object.
        """
        self.doc = doc
        self.identifiers = dict()

    def to_json(self) -> JSON:
        """Get the JSON description of this dataset.

        Returns:
            The JSON description of the dataset.
        """
        return self.doc

    def to_dcat(self) -> Graph:
        """Get the DCAT description of this dataset.

        Returns:
            An RDFLib graph containing a DCAT description of the dataset.
        """
        g = Graph()
        for method in self.get_topologically_sorted_parsing_methods():
            results = (
                x.value for x in parse(method.dataset_parsing_path).find(self.doc)
            )
            triples = itertools.chain(
                *(method(doc_or_value) for doc_or_value in results)
            )
            # Uncomment for a list of methods executed and the triples they
            #  produced.
            # print(method)
            for triple in triples:
                # print(triple)
                g.add(triple)
        return g

    def to_dcat_file(self, filename: str):
        """Export the DCAT description of the dataset to a file

        Args:
            filename (str): filename (with extension) for the export
        """
        g = self.to_dcat()
        g.serialize(destination=filename)

    def get_topologically_sorted_parsing_methods(self) -> tuple[callable, ...]:
        """Methods of this class that parse a JSON representation.

        Returns:
            A tuple of methods of this class that parse the JSON
            representation of the dataset, topologically sorted (the order
            is assigned using the `provides` and `requires` decorators).
        """
        dataset_parsing_methods: list[callable] = [
            function_or_attribute
            for item in dir(self)
            if hasattr(
                function_or_attribute := getattr(self, item), "dataset_parsing_path"
            )
        ]

        requirements = self._requirements
        provided = self._provided

        directed_edges = {
            (requirement, provided_item)
            for method in dataset_parsing_methods
            for requirement in requirements(method)
            for provided_item in provided(method)
        }
        sorted_provided = topological_sort(directed_edges)
        sorted_methods = tuple(
            sorted(
                dataset_parsing_methods,
                key=lambda method: min(
                    sorted_provided.index(x) for x in provided(method)
                ),
            )
        )
        return sorted_methods

    @staticmethod
    def _provided(method: callable) -> set[Union[callable, str]]:
        """Labels provided by a method.

        This is a helper method for `get_topologically_sorted_parsing_methods`.

        When no label is provided, the method itself is considered a label.

        Returns:
            Set of labels (or method itself) that the method provides.
        """
        return (
            method.dataset_parsing_provides
            if hasattr(method, "dataset_parsing_provides")
            else {method}
        )

    @staticmethod
    def _requirements(method: callable) -> set[str]:
        """Labels required by a method.

        This is a helper method for `get_topologically_sorted_parsing_methods`.

        Returns:
            Set of labels required by the method. When no labels are
            required, {None} is returned, because `None` means "do not
            care about the ordering" for the topological sorting
            algorithm's implementation.
        """
        if hasattr(method, "dataset_parsing_requires") and (
            contents := method.dataset_parsing_requires
        ):
            required = contents if contents else {None}
        else:
            required = {None}
        return required

    @provides("dataset")
    @requires("publisher")
    @jsonpath("$")
    def general_dataset(self, doc: JSON) -> set[Triple]:
        """Compute the triples for the dataset object itself.

        Args:
            doc: Child of dataset JSON representation determined by the JSON
                path provided to the `jsonpath` decorator that is applied to
                this function.

        Returns:
            The triples representing the dataset entity.
        """
        self.identifiers["dataset"] = (dataset := BNode())
        print(doc["latestVersion"])
        # Find URL in license, if not strip HTML.
        license_string = doc["latestVersion"]["termsOfUse"]
        if match := rfc3987.search(license_string):
            license_string = match.string[match.start() : match.end()]
            license_datatype = XSD.anyURI
        else:
            license_string = html_to_text(license_string)
            license_datatype = XSD.string

        triples = {
            (dataset, RDF.type, DCAT.Dataset),
            (
                dataset,
                DCTERMS.identifier,
                Literal(doc["persistentUrl"], datatype=XSD.anyURI),
            ),
            (
                dataset,
                DCTERMS.issued,
                Literal(doc["publicationDate"], datatype=XSD.date),
            ),
            (
                dataset,
                DCTERMS.modified,
                Literal(doc["latestVersion"]["lastUpdateTime"], datatype=XSD.dateTime),
            ),
            (dataset, DCTERMS.publisher, self.identifiers["publisher"]),
            (
                dataset,
                PAV.version,
                version_number := Literal(
                    ".".join(
                        str(x)
                        for x in (
                            doc["latestVersion"]["versionNumber"],
                            doc["latestVersion"]["versionMinorNumber"],
                        )
                    ),
                    datatype=XSD.string,
                ),
            ),
            (dataset, OWL.versionInfo, version_number),
            (
                dataset,
                DCTERMS.license,
                Literal(license_string, datatype=license_datatype),
            ),
        }
        if doc["latestVersion"]["license"].upper() != "NONE":
            triples |= {(dataset, DCTERMS.license, doc["license"])}
        return triples

    @provides("publisher")
    @jsonpath("$.publisher")
    def general_publisher(self, publisher: str) -> set[Triple]:
        """Compute the triples for the publisher entity.

        Args:
            publisher: Name of the publisher.

        Returns:
            The triples representing the publisher entity.
        """
        self.identifiers["publisher"] = (publisher_id := BNode())
        return {
            (publisher_id, RDF.type, FOAF.Agent),
            (publisher_id, FOAF.name, Literal(publisher, datatype=XSD.string)),
        }

    @requires("dataset")
    @jsonpath(
        "$.latestVersion.metadataBlocks.citation.fields" '[?(@.typeName == "title")]'
    )
    def block_citation_title(self, doc: JSON) -> set[Triple]:
        """Compute the triple defining the title of the dataset.

        Args:
            doc: Child of dataset JSON representation determined by the JSON
                path provided to the `jsonpath` decorator that is applied to
                this function.

        Returns:
            The triple representing the title of the dataset.
        """
        return {
            (
                self.identifiers["dataset"],
                DCTERMS.title,
                Literal(doc["value"], datatype=XSD.string),
            ),
        }

    @requires("dataset")
    @jsonpath(
        "$.latestVersion.metadataBlocks.citation.fields"
        '[?(@.typeName == "alternativeTitle")]'
    )
    def block_citation_alternative_title(self, doc: JSON) -> set[Triple]:
        """Compute the triples for an alternative title of the dataset.

        Args:
            doc: Child of dataset JSON representation determined by the JSON
                path provided to the `jsonpath` decorator that is applied to
                this function.

        Returns:
            The triples representing an alternative title for the dataset.
        """
        return {
            (
                self.identifiers["dataset"],
                DCTERMS.title,
                Literal(doc["value"], datatype=XSD.string),
            ),
        }

    @requires("dataset")
    @jsonpath(
        "$.latestVersion.metadataBlocks.citation.fields" '[?(@.typeName == "author")]'
    )
    def block_citation_author(self, doc: JSON) -> set[Triple]:
        """Compute the triples for an author entity.

        Additionally, connects it to the dataset.

        Args:
            doc: Child of dataset JSON representation determined by the JSON
                path provided to the `jsonpath` decorator that is applied to
                this function.

        Returns:
            The triples representing the author entity.
        """
        triples = set()
        for author in doc["value"]:

            author_name = (
                author["authorName"]["value"] if "authorName" in author else None
            )

            author_affiliation = (
                author["authorAffiliation"]["value"]
                if "authorAffiliation" in author
                else None
            )

            author_type = (
                FOAF.Agent
                if author_affiliation is not None
                and (not author_affiliation.lower() == author_name.lower())
                else FOAF.Organization
            )
            if author_type == FOAF.Organization:
                author_affiliation = None

            triples |= {(author_identifier := BNode(), RDF.type, author_type)}
            if author_affiliation:
                triples |= {
                    (organization := BNode(), RDF.type, FOAF.Organization),
                    (author_identifier, FOAF.member, organization),
                }
        return triples

    @requires("dataset")
    @jsonpath(
        "$.latestVersion.metadataBlocks.citation.fields"
        '[?(@.typeName == "datasetContact")]'
    )
    def block_citation_dataset_contact(self, doc: JSON) -> set[Triple]:
        """Compute the triples describing a contact entity for the dataset.

        Args:
            doc: Child of dataset JSON representation determined by the JSON
                path provided to the `jsonpath` decorator that is applied to
                this function.

        Returns:
            The triples representing the contact person
        """
        triples = set()
        for contact in doc["value"]:
            contact_name = (
                contact["datasetContactName"]["value"]
                if "datasetContactName" in contact
                else None
            )

            contact_affiliation = (
                contact["datasetContactAffiliation"]["value"]
                if "datasetContactAffiliation" in contact
                else None
            )

            contact_type = (
                FOAF.Agent
                if not contact_affiliation.lower() == contact_name.lower()
                else FOAF.Organization
            )
            if contact_type == FOAF.Organization:
                contact_affiliation = None

            contact_email = (
                contact["datasetContactEmail"]["value"]
                if "datasetContactEmail" in contact
                else None
            )

            contact_identifier = BNode()
            if contact_type == FOAF.Organization:
                triples |= {
                    (contact_identifier, RDF.type, VCARD.Organization),
                }
            else:
                triples |= {
                    (contact_identifier, RDF.type, VCARD.Kind),
                }

            if contact_affiliation:
                triples |= {
                    (
                        contact_identifier,
                        VCARD["organization-name"],
                        Literal(contact_affiliation, datatype=XSD.string),
                    ),
                }

            triples |= {
                (
                    contact_identifier,
                    VCARD.fn,
                    Literal(contact_name, datatype=XSD.string),
                )
            }
            if contact_email:
                triples |= {
                    (
                        contact_identifier,
                        VCARD.hasEmail,
                        URIRef(f"mailto:{contact_email}"),
                    )
                }

            triples |= {
                (self.identifiers["dataset"], DCAT.contactPoint, contact_identifier)
            }
        return triples

    @requires("dataset")
    @jsonpath(
        "$.latestVersion.metadataBlocks.citation.fields"
        '[?(@.typeName == "dsDescription")]'
    )
    def block_citation_description(self, doc: JSON) -> set[Triple]:
        """Compute the triples for a description of the dataset.

        Args:
            doc: Child of dataset JSON representation determined by the JSON
                path provided to the `jsonpath` decorator that is applied to
                this function.

        Returns:
            The triples representing the description.
        """
        triples = set()
        for description in doc["value"]:
            value = description["dsDescriptionValue"]["value"]
            value = None if value == "value unavailable" else value

            if value is None:
                continue

            if "dsDescriptionDate" in description:
                value += (
                    f"(Description provided on " f"{description['dsDescriptionDate']})"
                )

            triples |= {
                (
                    self.identifiers["dataset"],
                    DCTERMS.description,
                    Literal(value, datatype=XSD.string),
                )
            }
        return triples

    @requires("dataset")
    @jsonpath(
        "$.latestVersion.metadataBlocks.citation.fields" '[?(@.typeName == "language")]'
    )
    def block_citation_language(self, doc: JSON) -> set[Triple]:
        """Compute the triples describing one of the languages of the dataset.

        Uses several auxiliary attributes located just below this method.

        Args:
            doc: Child of dataset JSON representation determined by the JSON
                path provided to the `jsonpath` decorator that is applied to
                this function.

        Returns:
            The triples representing the language.
        """
        triples = set()

        # A dataset may have multiple languages.
        for language in doc["value"]:
            # Even multiple names may come separated via a comma for the
            #  same language.
            names = language.split(",")
            names = (name.strip() for name in names)
            # Some names are exclusive to the Dataverse, translate to
            # ISO-639 english names.
            names = (
                self.block_citation_language_synonyms_Dataverse.get(name, name)
                for name in names
            )
            # This name may be the one supported by `pycountry`, or not,
            #  therefore we add all possibilities to the iterator.
            names = (
                name
                for main_name in names
                for name in itertools.chain(
                    (main_name,),
                    self.block_citation_language_synonyms_ISO.get(main_name, set()),
                )
            )

            # Finally, loop over all the possibilities and try to find a match.
            #  Then create the triple according to
            #  https://www.w3.org/TR/vocab-dcat-2/#Property:language.
            #
            #  A two-letter code will always be defined for any language
            #  received, because it should be in ISO 639-1. However,
            #  when the value is 'Not applicable' or 'Not linguistic
            #  content', the three-letter code should be used.
            result = None
            for name in names:

                if name.lower() in {
                    "No linguistic content".lower(),
                    "Not applicable".lower(),
                }:
                    result = "zxx"
                    break

                result = pycountry.languages.get(name=name)
                if result is not None:
                    result = result.alpha_2
                    break

            if result is None:
                raise ValueError(f"Unsupported language {language}.")

            result = URIRef(
                f"http://id.loc.gov/vocabulary/"
                f"iso639-{1 if len(result) <= 2 else 2}"
                f"/%s" % result
            )

            result = (self.identifiers["dataset"], DCTERMS.language, result)

            triples.add(result)

        return triples

    # - Dataverse theoretically conforms to ISO 639-1, but actually, not all
    #   language names provided belong to the "All English Names" column for
    #   languages represented by ISO 639-1. For example `Greek (Modern)`
    #   from he Dataverse is 'Modern Greek (1453-)' on ISO 639-1.
    #   See https://github.com/IQSS/dataverse/blob/
    #   9161cd6c5d9665b2a7b8c14b8e726a6712093ee0/scripts/api/data/
    #   metadatablocks/citation.tsv

    # - Moreover, the `pycountry` library only accepts one of the official
    #   names from https://www.loc.gov/standards/iso639-2/php/English_list.php.
    #   Dataverse may refer to the language with a different official name.

    # - Finally `pycountry` uses the underlying OS library, so one should
    #   not trust that the same official name will be associated to the same
    #   language across all operating systems.

    # Therefore, it makes sense to create lists of synonyms to mitigate the
    # above problems.

    # All ISO 639-1 official names for languages with more than one official
    # name. As all synonyms have the same importance, they are first
    # specified as sets, and then later transformed to a hash table for fast
    # access.
    block_citation_language_synonyms_ISO_sets = {
        frozenset({"Castillian", "Spanish"}),
        frozenset({"Catalan", "Valencian"}),
        frozenset({"Chichewa", "Chewa", "Nyanja"}),
        frozenset({"Zhuang", "Chuang"}),
        frozenset(
            {
                "Church Slavic",
                "Old Slavonic",
                "Church Slavonic",
                "Old Bulgarian",
                "Old Church Slavonic",
            }
        ),
        frozenset({"Divehi", "Dhivehi", "Maldivian"}),
        frozenset({"Dutch", "Flemish"}),
        frozenset({"Gaelic", "Scottish Gaelic"}),
        frozenset({"Kikuyu", "Gikuyu"}),
        frozenset({"Kalaallisut", "Greenlandic"}),
        frozenset({"Haitian", "Haitian Creole"}),
        frozenset({"Kuanyama", "Kwanyama"}),
        frozenset({"Kirghiz", "Kyrgyz"}),
        frozenset({"Limburgan", "Limburger", "Limburgish"}),
        frozenset({"Romanian", "Moldavian", "Moldovan"}),
        frozenset({"Navajo", "Navaho"}),
        frozenset({"Ndebele, North", "North Ndebele"}),
        frozenset({"Ndebele, South", "South Ndebele"}),
        frozenset({"Norwegian Nynorsk", "Nynorsk, Norwegian"}),
        frozenset({"Sichuan Yi", "Nuosu"}),
        frozenset({"Interlingue", "Occidental"}),
        frozenset({"Ossetian", "Ossetic"}),
        frozenset({"Panjabi", "Punjabi"}),
        frozenset({"Pushto", "Pashto"}),
        frozenset({"Sinhala", "Sinhalese"}),
        frozenset({"Uighur", "Uyghur"}),
    }
    block_citation_language_synonyms_ISO = {
        name: name_set - {name}
        for name_set in block_citation_language_synonyms_ISO_sets
        for name in name_set
    }
    del block_citation_language_synonyms_ISO_sets

    # Synonyms for Dataverse non-official names, format: Dict[str, str],
    # {'dataverse_name': 'one_of_the_official_names'}.
    block_citation_language_synonyms_Dataverse = {
        "Bangla": "Bengali",
        "Fula": "Fulah",
        "Pulaar": "Fulah",
        "Pular": "Fulah",
        "Letzeburgesch": "Luxembourgish",
        "Persian (Farsi)": "Persian",
        "Sanskrit (Saṁskṛta)": "Sanskrit",
        "Tibetan Standard": "Tibetan",
        "Tibetan, Central": "Tibetan",
    }

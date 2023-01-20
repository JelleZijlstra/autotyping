from typing import Tuple, Optional, List
import re


# strategy heavily inspired by
# https://github.com/Zac-HD/hypothesis/blob/07ff885edaa0c11f480a8639a75101c6fe14844f/hypothesis-python/src/hypothesis/extra/ghostwriter.py#L319
def guess_type_from_argname(name: str) -> Tuple[Optional[str], List[str]]:
    """
    If all else fails, we try guessing a strategy based on common argument names.

    A "good guess" is _usually correct_, and _a reasonable mistake_ if not.
    The logic below is therefore based on a manual reading of the builtins and
    some standard-library docs, plus the analysis of about three hundred million
    arguments in https://github.com/HypothesisWorks/hypothesis/issues/3311
    """

    containers = "deque|list|set|iterator|tuple|iter|iterable"
    # not using 'sequence', 'counter' or 'collection' due to likely false alarms

    # (container)_(int|float|str|bool)s?
    # e.g. list_ints => List[int]
    # only check for built-in types to avoid false alarms, e.g. list_create, list_length
    m = re.fullmatch(
        rf"(?P<container>{containers})_(?P<elems>int|float|str|bool)s?", name
    )
    if m:  # mfw 3.7 doesn't have the walrus operator :(
        container_type = m.group("container").capitalize()
        if container_type == "Iter":
            container_type = "Iterable"
        return m.group("elems"), [container_type]

    # <name>s?_(container)
    # e.g. latitude_list => List[float]
    # (container)_of_<name>(s)
    # e.g. set_of_widths => Set[int]
    m = re.fullmatch(
        rf"(?P<elems>\w*?)_?(?P<container>{containers})", name
    ) or re.fullmatch(rf"(?P<container>{containers})_of_(?P<elems>\w*)", name)
    if m:
        # only do a simple container match
        # and don't check all of BOOL_NAMES to not trigger on stuff like "save_list"
        elems = m.group("elems")
        for names, name_type in (
            (("bool", "boolean"), "bool"),
            # don't trigger on `real_list`
            (FLOAT_NAMES - {"real"}, "float"),
            (INTEGER_NAMES, "int"),
            (STRING_NAMES | {"string", "str"}, "str"),
        ):
            if elems in names or (elems[-1] == "s" and elems[:-1] in names):
                return name_type, [m.group("container").capitalize()]

    # Names which imply the value is a boolean
    if name.startswith("is_") or name in BOOL_NAMES:
        return "bool", []

    if (
        name.endswith("_size")
        or (name.endswith("size") and "_" not in name)
        or re.fullmatch(r"n(um)?_[a-z_]*s", name)
        or name in INTEGER_NAMES
    ):
        return "int", []

    if name in FLOAT_NAMES:
        return "float", []

    if (
        "file" in name
        or "path" in name
        or name.endswith("_dir")
        or name in ("fname", "dir", "dirname", "directory", "folder")
    ):
        # Common names for filesystem paths: these are usually strings, but we
        # don't want to make strings more convenient than pathlib.Path.
        return None, []

    if (
        name.endswith("_name")
        or (name.endswith("name") and "_" not in name)
        or ("string" in name and "as" not in name)
        or name.endswith("label")
        or name in STRING_NAMES
    ):
        return "str", []

    # Last clever idea: maybe we're looking a plural, and know the singular:
    # don't trigger on multiple ending "s" to avoid nested calls
    if re.fullmatch(r"\w*[^s]s", name):
        elems, container = guess_type_from_argname(name[:-1])
        if elems is not None and not container:
            return elems, ["Sequence"]

    return None, []


BOOL_NAMES = {
    "keepdims",
    "verbose",
    "debug",
    "force",
    "train",
    "training",
    "trainable",
    "bias",
    "shuffle",
    "show",
    "load",
    "pretrained",
    "save",
    "overwrite",
    "normalize",
    "reverse",
    "success",
    "enabled",
    "strict",
    "copy",
    "quiet",
    "required",
    "inplace",
    "recursive",
    "enable",
    "active",
    "create",
    "validate",
    "refresh",
    "use_bias",
}
INTEGER_NAMES = {
    "width",
    "size",
    "length",
    "limit",
    "idx",
    "stride",
    "epoch",
    "epochs",
    "depth",
    "pid",
    "steps",
    "iteration",
    "iterations",
    "vocab_size",
    "ttl",
    "count",
    "offset",
    "seed",
    "dim",
    "total",
    "priority",
    "port",
    "number",
    "num",
    "int",
}
FLOAT_NAMES = {
    "real",
    "imag",
    "alpha",
    "theta",
    "beta",
    "sigma",
    "gamma",
    "angle",
    "reward",
    "learning_rate",
    "dropout",
    "dropout_rate",
    "epsilon",
    "eps",
    "prob",
    "tau",
    "temperature",
    "lat",
    "latitude",
    "lon",
    "longitude",
    "radius",
    "tol",
    "tolerance",
    "rate",
    "treshold",
    "float",
}
STRING_NAMES = {
    "text",
    "txt",
    "password",
    "label",
    "prefix",
    "suffix",
    "desc",
    "description",
    "str",
    "pattern",
    "subject",
    "reason",
    "comment",
    "prompt",
    "sentence",
    "sep",
    "host",
    "hostname",
    "email",
    "word",
    "slug",
    "api_key",
    "char",
    "character",
}

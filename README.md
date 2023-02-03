When I refactor code I often find myself tediously adding type
annotations that are obvious from context: functions that don't
return anything, boolean flags, etcetera. That's where autotyping
comes in: it automatically adds those types and inserts the right
annotations.

It is built as a LibCST codemod; see the
[LibCST documentation](https://libcst.readthedocs.io/en/latest/codemods_tutorial.html)
for more information on how to use codemods.

# Usage

Here's how to use it:

- `pip install autotyping`
- Make sure you have a `.libcst.codemod.yaml` with `'autotyping'` in the `modules` list.
  For an example, see the `.libcst.codemod.yaml` in this repo.
- Run `python -m libcst.tool codemod autotyping.AutotypeCommand /path/to/my/code`

By default it does nothing; you have to add flags to make it do
more transformations. The following are supported:

- Annotating return types:
  - `--none-return`: add a `-> None` return type to functions without any
    return, yield, or raise in their body
  - `--scalar-return`: add a return annotation to functions that only return
    literal bool, str, bytes, int, or float objects.
- Annotating parameter types:
  - `--bool-param`: add a `: bool` annotation to any function
    parameter with a default of `True` or `False`
  - `--int-param`, `--float-param`, `--str-param`, `--bytes-param`: add
    an annotation to any parameter for which the default is a literal int,
    float, str, or bytes object
  - `--annotate-optional foo:bar.Baz`: for any parameter of the form
    `foo=None`, add `Baz`, imported from `bar`, as the type. For example,
    use `--annotate-optional uid:my_types.Uid` to annotate any `uid` in your
    codebase with a `None` default as `Optional[my_types.Uid]`.
  - `--annotate-named-param foo:bar.Baz`: annotate any parameter with no
    default that is named `foo` with `bar.Baz`. For example, use
    `--annotate-named-param uid:my_types.Uid` to annotate any `uid`
    parameter in your codebase with no default as `my_types.Uid`.
  - `--guess-common-names`: infer certain parameter types from their names
    based on common patterns in open-source Python code. For example, infer
    that a `verbose` parameter is of type `bool`.
- Annotating magical methods:
  - `--annotate-magics`: add type annotation to certain magic methods.
    Currently this does the following:
    - `__str__` returns `str`
    - `__repr__` returns `str`
    - `__len__` returns `int`
    - `__length_hint__` returns `int`
    - `__init__` returns `None`
    - `__del__` returns `None`
    - `__bool__` returns `bool`
    - `__bytes__` returns `bytes`
    - `__format__` returns `str`
    - `__contains__` returns `bool`
    - `__complex__` returns `complex`
    - `__int__` returns `int`
    - `__float__` returns `float`
    - `__index__` returns `int`
    - `__exit__`: the three parameters are `Optional[Type[BaseException]]`,
      `Optional[BaseException]`, and `Optional[TracebackType]`
    - `__aexit__`: same as `__exit__`
  - `--annotate-imprecise-magics`: add imprecise type annotations for
    some additional magic methods. Currently this adds `typing.Iterator`
    return annotations to `__iter__`, `__await__`, and `__reversed__`.
    These annotations should have a generic parameter to indicate what
    you're iterating over, but that's too hard for autotyping to figure
    out.
- External integrations
  - `--pyanalyze-report`: takes types suggested by
    [pyanalyze](https://github.com/quora/pyanalyze)'s `suggested_parameter_type`
    and `suggested_return_type` codes and applies them.
  - `--only-without-imports`: only apply pyanalyze suggestions that do not require
    new imports. This is useful because suggestions that require imports may need
    more manual work.

There are two shortcut flags to enable multiple transformations at once:

- `--safe` enables changes that should always be safe. This includes
  `--none-return`, `--scalar-return`, and `--annotate-magics`.
- `--aggressive` enables riskier changes that are more likely to produce
  new type checker errors. It includes all of `--safe` as well as `--bool-param`,
  `--int-param`, `--float-param`, `--str-param`, `--bytes-param`, and
  `--annotate-imprecise-magics`.

# Limitations

Autotyping is intended to be a simple tool that uses heuristics to find
annotations that would be tedious to add by hand. The heuristics may fail,
and after you run autotyping you should run a type checker to verify that
the types it added are correct.

Known limitations:

- autotyping does not model code flow through a function, so it may miss
  implicit `None` returns

# Changelog

## 23.2.0 (February 3, 2023)

- Add `--guess-common-names` (contributed by John Litborn)
- Fix the `--safe` and `--aggressive` flags so they don't take
  ignored arguments
- `--length-hint` should return `int` (contributed by Nikita Sobolev)
- Fix bug in import adding (contributed by Shantanu)

## 22.9.0 (September 5, 2022)

- Add `--safe` and `--aggressive`
- Add `--pyanalyze-report`
- Do not add `None` return types to methods marked with `@abstractmethod` and
  to methods in stub files
- Improve type inference:
  - `"string" % ...` is always `str`
  - `b"bytes" % ...` is always `bytes`
  - An `and` or `or` operator where left and right sides are of the same type
    returns that type
  - `is`, `is not`, `in`, and `not in` always return `bool`

## 21.12.0 (December 21, 2021)

- Initial PyPI release

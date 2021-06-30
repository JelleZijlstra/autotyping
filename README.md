When I refactor code I often find myself tediously adding type
annotations that are obvious from context: functions that don't
return anything, boolean flags, etcetera. That's where autotyper
comes in: it automatically adds those types and inserts the right
annotations.

It is built as a LibCST codemod; see the
[LibCST documentation](https://libcst.readthedocs.io/en/latest/codemods_tutorial.html)
for more information on how to use codemods.

Here's how I use it:

- Go to the autotype directory
- Run `python3 -m libcst.tool codemod autotype.AutotypeCommand /path/to/my/code`

By default it does nothing; you have to add flags to make it do
more transformations. The following are supported:

- `--none-return`: add a `-> None` return type to functions without any
  return, yield, or raise in their body
- `--bool-param`: add a `: bool` annotation to any function
  parameter with a default of `True` or `False`
- `--annotate-optional foo:bar.Baz`: for any parameter of the form
  `foo=None`, add `Baz`, imported from `bar`, as the type. For example,
  use `--annotate-optional uid:my_types.Uid` to annotate any `uid` in your
  codebase with a `None` default as `Optional[my_types.Uid]`.
- `--annotate-named-param foo:bar.Baz`: annotate any parameter with no
  default that is named `foo` with `bar.Baz`. For example, use
  `--annotate-named-param uid:my_types.Uid` to annotate any `uid`
  parameter in your codebase with no default as `my_types.Uid`.

Things to add:

- Infer asynq functions and if so add return types even if there is
  a yield in the function
- Infer `-> bool` as the return type if all return statements are
  `True`, `False`, or boolean expressions like `==`.
